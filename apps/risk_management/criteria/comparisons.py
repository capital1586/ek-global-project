import typing
import enum

from helpers.typing_utils import SupportsRichComparison
from .exceptions import ComparisonExecutorNotFound


class ComparisonOperator(enum.Enum):
    """An enumeration of comparison operators"""

    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_OR_EQUALS = ">="
    LESS_OR_EQUALS = "<="


_ComparisonExecutor = typing.Callable[
    [SupportsRichComparison, SupportsRichComparison], bool
]
"""Takes two objects, A and B. Returns a boolean result of a comparison of A against B"""

COMPARISON_EXECUTORS: typing.Dict[ComparisonOperator, _ComparisonExecutor] = {}
"""A mapping of comparison operators to their executors"""


def comparison_executor(op: ComparisonOperator):
    """
    Decorator to register a comparison executor for a comparison operator

    :param op: The comparison operator to register the executor for
    """
    op = ComparisonOperator(op)

    def _decorator(executor: _ComparisonExecutor):
        global COMPARISON_EXECUTORS

        COMPARISON_EXECUTORS[op] = executor
        return executor

    return _decorator


def get_comparison_executor(
    op: typing.Union[ComparisonOperator, str], *, raise_not_found: bool = True
) -> typing.Optional[_ComparisonExecutor]:
    """
    Get a comparison executor for a comparison operator

    :param op: The comparison operator to get the executor for
    :param raise_not_found: If True, raise an exception if no executor is found
    :return: The comparison executor or None if not found
    :raises ComparisonExecutorNotFound: If no executor is found and raise_not_found is True
    """
    op = ComparisonOperator(op)
    try:
        return COMPARISON_EXECUTORS[op]
    except KeyError:
        if not raise_not_found:
            return None
        raise ComparisonExecutorNotFound(
            f"No executor was found for operator, '{op.value}'."
        )


@comparison_executor(ComparisonOperator.GREATER_THAN)
def greater_than(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is greater than B"""
    return a > b


@comparison_executor(ComparisonOperator.LESS_THAN)
def less_than(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is less than B"""
    return a < b


@comparison_executor(ComparisonOperator.EQUALS)
def equals(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is equal to B"""
    return a == b


@comparison_executor(ComparisonOperator.NOT_EQUALS)
def not_equals(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is not equal to B"""
    return a != b


@comparison_executor(ComparisonOperator.GREATER_OR_EQUALS)
def greater_or_equals(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is greater than or equal to B"""
    return a >= b


@comparison_executor(ComparisonOperator.LESS_OR_EQUALS)
def less_or_equals(a: SupportsRichComparison, b: SupportsRichComparison) -> bool:
    """Checks if A is less than or equal to B"""
    return a <= b
