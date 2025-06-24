import asyncio
import typing
import uuid
import enum
import attrs
import cattrs
from asgiref.sync import sync_to_async

from helpers.utils.time import timeit

from .functions import FunctionSpec, evaluate as evaluate_function, make_function_spec
from .comparisons import ComparisonOperator, get_comparison_executor
from .exceptions import UnsupportedFunction
from . import converter, type_cast


T = typing.TypeVar("T")


class CriterionStatus(enum.IntEnum):
    """Status of a criterion evaluation"""

    PASSED = 1
    FAILED = 0


@type_cast
@attrs.define(auto_attribs=True, slots=True, frozen=True, repr=False, hash=False)
class Criterion:
    """A criterion for evaluating a condition"""

    id: uuid.UUID = attrs.field(default=uuid.uuid4, kw_only=True, repr=str)
    """A unique identifier for the criterion"""
    func1: FunctionSpec
    """The first function to evaluate"""
    func2: FunctionSpec
    """The second function to evaluate"""
    op: ComparisonOperator
    """The operator to use for comparing results of func1 and func2"""

    def __repr__(self) -> str:
        return f"<Criterion_{self.id.hex}: {repr(self.func1)} {self.op.value} {repr(self.func2)}>"

    def __str__(self) -> str:
        return f"{self.func1.name} {self.op.value} {self.func2.name}"

    def __hash__(self) -> int:
        return hash(self.id)


@attrs.define(auto_attribs=True, slots=True, hash=False)
class Criteria:
    """A collection of criterion"""

    criterion_list: typing.List[Criterion] = attrs.field(default=list)

    def get(self, id: uuid.UUID) -> typing.Optional[Criterion]:
        """Get a criterion by its id"""
        for criterion in self.criterion_list:
            if criterion.id == id:
                return criterion
        return None

    def index(self, criterion: Criterion) -> int:
        """Get the index of a criterion"""
        return self.criterion_list.index(criterion)

    def count(self) -> int:
        """Get the number of criterions"""
        return len(self)

    def remove(self, criterion: Criterion):
        """Remove a criterion from the criteria"""
        return remove_criterion(self, criterion)

    def __hash__(self) -> int:
        return hash(tuple(self.criterion_list))

    def __contains__(self, criterion: Criterion) -> bool:
        return criterion in self.criterion_list

    def __len__(self) -> int:
        return len(self.criterion_list)

    # Allows iteration over criterion_list directly with the criteria object
    def __iter__(self):
        return iter(self.criterion_list)

    def __bool__(self):
        return bool(self.criterion_list)

    def __getitem__(self, index: int):
        return self.criterion_list[index]

    def __add__(self, other):
        if isinstance(other, Criteria):
            return merge_criterias(self, other)

        elif isinstance(other, Criterion):
            return add_criterion(self, other)
        raise TypeError(
            f"unsupported operand type(s) for +: '{type(self)}' and '{type(other)}'"
        )

    def __sub__(self, other):
        if isinstance(other, Criterion):
            return remove_criterion(self, other)
        raise TypeError(
            f"unsupported operand type(s) for -: '{type(self)}' and '{type(other)}'"
        )

    __iadd__ = __add__
    __isub__ = __sub__


def add_criterion(criteria: Criteria, criterion: Criterion) -> Criteria:
    """
    Add a criterion to the criteria, if it does not already exist

    :param criteria: The criteria to add the criterion to
    :param criterion: The criterion to add
    :return: A new criteria with the added criterion
    """
    criterion_set = set(criteria)
    criterion_set.add(criterion)
    return Criteria(list(criterion_set))


def remove_criterion(criteria: Criteria, *criterion: Criterion) -> Criteria:
    """
    Remove a criterion from the criteria, if it exists

    :param criteria: The criteria to remove the criterion from
    :param criterion: The criterion or set of criterion to remove
    :return: A new criteria with the removed criterion or criterion set
    """
    if not criterion:
        return criteria

    criterion_set = set(criteria)
    diff_criterion_set = criterion_set - criterion
    return Criteria(list(diff_criterion_set))


def merge_criterias(*criterias: Criteria) -> Criteria:
    """Merge multiple criterias into a single criteria"""
    criterion_list = []
    for criteria in criterias:
        criterion_list.extend(criteria)

    # Convert to set to remove duplicate,
    # since criterion with the same id have the same hash
    criterion_set = set(criterion_list)
    return Criteria(list(criterion_set))


def make_criterion(
    *,
    func1: typing.Dict[str, typing.Any],
    func2: typing.Dict[str, typing.Any],
    op: str,
    id: typing.Optional[uuid.UUID] = None,
    ignore_unsupported_func: bool = False,
) -> Criterion:
    """
    Helper function to create a criterion from function specification data and an operator

    Performs validation on the functions and raises an exception if the functions are not supported

    :param func1: The first function to evaluate
    :param func2: The second function to evaluate
    :param op: The operator to use for comparing the results of the functions
    :param id: A unique identifier for the criterion, defaults to a new UUID
    :param ignore_unsupported_func: If True, do not raise an exception if the functions are not supported
    :return: A new criterion
    :raises UnsupportedFunction: If the functions are not supported and ignore_unsupported_func is False
    """
    try:
        func1 = make_function_spec(func1["name"], **(func1.get("kwargs", None) or {}))
        func2 = make_function_spec(func2["name"], **(func2.get("kwargs", None) or {}))
    except UnsupportedFunction:
        if not ignore_unsupported_func:
            raise

    kwds = {
        "func1": func1,
        "func2": func2,
        "op": ComparisonOperator(op),
    }
    if id:
        kwds["id"] = id
    return Criterion(**kwds)


def update_criterion(criterion: Criterion, **kwds) -> Criterion:
    """
    Update a criterion with new attributes

    :param criterion: The criterion to update
    :param kwds: The new attributes to update with
    :return: A new criterion with the updated attributes
    """
    kwds.setdefault("ignore_unsupported_func", True)
    kwds.pop("id", None)

    old_attrs = cattrs.unstructure(criterion)
    kwargs = {**old_attrs, **kwds}
    return make_criterion(**kwargs)


def evaluate_criterion(
    o: T, /, criterion: Criterion, *, ignore_unsupported_func: bool = False
):
    """
    Run a criterion evaluation on an object

    :param o: The object to evaluate the criterion on
    :param criterion: The criterion to evaluate
    :param ignore_unsupported_func: If True, an exception will not be raised
        if any function in the criterion is not supported.
        The criterion will be evaluated as failed
    :return: The status of the criterion evaluation
    """
    try:
        a = evaluate_function(o, criterion.func1)
        b = evaluate_function(o, criterion.func2)
    except UnsupportedFunction:
        if ignore_unsupported_func:
            return CriterionStatus.FAILED
        raise

    comparison_executor = get_comparison_executor(criterion.op)
    return (
        CriterionStatus.PASSED if comparison_executor(a, b) else CriterionStatus.FAILED
    )


# def evaluate_criteria(
#     o: T, /, criteria: Criteria, *, ignore_unsupported_func: bool = False
# ) -> typing.Dict[str, CriterionStatus]:
#     """
#     Run multiple criterion evaluations on an object.
#     The criterions are evaluated concurrently and so should be independent of each other

#     :param o: The object to evaluate the criteria on
#     :param criteria: The criteria containing the criterions to evaluate
#     :param ignore_unsupported_func: If True, an exception will not be raised if any
#         function in a criterion is not supported. The criterion will be evaluated as failed
#     :return: A dictionary of the criterion and their evaluation status
#     """
#     if not criteria:
#         return {}

#     async def main() -> typing.List[CriterionStatus]:
#         async_evaluate_criterion = sync_to_async(evaluate_criterion)
#         tasks = []
#         for criterion in criteria:
#             task = asyncio.create_task(
#                 async_evaluate_criterion(
#                     o, criterion, ignore_unsupported_func=ignore_unsupported_func
#                 )
#             )
#             tasks.append(task)
#         return await asyncio.gather(*tasks)

#     statuses = asyncio.run(main())
#     result = {}
#     for criterion, status in zip(criteria, statuses):
#         result[str(criterion)] = status
#     return result


# @timeit
def evaluate_criteria(
    o: T, /, criteria: Criteria, *, ignore_unsupported_func: bool = False
) -> typing.Dict[str, CriterionStatus]:
    """
    Run multiple criterion evaluations on an object.
    The criterions are evaluated sequentially using a regular for loop.

    :param o: The object to evaluate the criteria on
    :param criteria: The criteria containing the criterions to evaluate
    :param ignore_unsupported_func: If True, an exception will not be raised if any
        function in a criterion is not supported. The criterion will be evaluated as failed
    :return: A dictionary of the criterion and their evaluation status
    """
    if not criteria:
        return {}

    statuses = []
    for criterion in criteria:
        status = evaluate_criterion(
            o, criterion, ignore_unsupported_func=ignore_unsupported_func
        )
        statuses.append(status)

    result = {}
    for criterion, status in zip(criteria, statuses):
        result[str(criterion)] = status

    return result


def load_criteria_from_list(criterion_list: typing.List[typing.Dict[str, typing.Any]]):
    """
    Load criteria from a list of criterion data

    :param criterion_list: A list of criterion data.
        Usually from a JSON object return by `converter.unstructure`
    :return: A criteria object
    """
    return converter.structure({"criterion_list": criterion_list}, Criteria)
