from typing import Union, TypeVar, List, Mapping, Any, Generic
from django.db import models
from django.db.models.manager import BaseManager
from django.http import request
from rest_framework import exceptions


M = TypeVar("M", bound=models.Model)


class QueryDictQuerySetFilterer(Generic[M]):
    """
    Filters a queryset based on query parameters in a QueryDict

    Add a new method `parse_<key>` for each query parameter that needs to be parsed and applied as a filter.
    Each `parse_<key>` method should accept a single argument and return a `django.db.models.Q` object representing
    the filter to be applied. The `parse_<key>` method should raise an `ParseError` if the value
    is invalid or cannot be parsed.

    Example:
    ```python
    class MyFilterer(QueryDictQuerySetFilterer):
        ...
        def parse_new_param(self, value: str) -> models.Q:
            # Convert value to appropriate type and
            # return a dictionary containing the filter
            return models.Q(new_param=value)
    ```

    If there is an error you should raise a `ParseError` with a list of error messages.

    For example:
    ```python
    class MyFilterer(QueryDictQuerySetFilterer):
        ...
        def parse_new_param(self, value: str) -> models.Q:
            errors = []
            if not value.isdigit():
                errors.append("Value must be an integer")
            if errors:
                raise self.ParseError(errors)
            return models.Q(new_param=int(value))
    ```
    """

    class ParseError(exceptions.ValidationError):
        """Error raised when parsing query parameters fails"""

        default_detail = "Error parsing query parameter(s)"

    def __init__(self, querydict: Union[request.QueryDict, Mapping[str, Any]]) -> None:
        """
        Create a new instance

        :param querydict: QueryDict containing filters(query params) to be applied
        """
        self._error_dict: Mapping[str, List[str]] = {}
        self.q = self.parse_querydict(querydict)

    def parse_querydict(
        self, querydict: Union[request.QueryDict, Mapping[str, Any]]
    ) -> models.Q:
        """
        Clean and parse querydict containing filters

        This method iterates over each key-value pair in the querydict and calls the corresponding
        `parse_<key>` method to clean and parse the value. The cleaned query filters are then combined
        using the AND operator.

        :param querydict: QueryDict containing filters(query params) to be applied
        :return: Combined query filters
        """
        aggregate = models.Q()
        for key, value in querydict.items():
            if not value:
                # Skip empty values
                continue
            try:
                query_filter = getattr(self, f"parse_{key}")(value)
            except AttributeError:
                # Method for parsing the query parameter was not implemented
                continue
            except self.ParseError as exc:
                self._error_dict[key] = exc.detail
            else:
                if not isinstance(query_filter, models.Q):
                    raise TypeError(
                        f"parse_{key} method must return a `django.db.models.Q` object."
                    )
                aggregate.add(query_filter, models.Q.AND)
        return aggregate

    def apply_filters(
        self,
        qs: Union[BaseManager[M], models.QuerySet[M]],
        *,
        raise_errors: bool = True,
    ) -> models.QuerySet[M]:
        """
        Apply query filters to queryset

        :param qs: Unfiltered queryset
        :param raise_errors: If True, raise a ParseError if there were errors parsing the query parameters
        :return: Filtered queryset
        :raises: ParseError if there were errors parsing the query parameters
        """
        if self._error_dict and raise_errors is True:
            raise self.ParseError(self._error_dict)
        return qs.filter(self.q)

    def parse_none(self, value: str) -> models.Q:
        """Dummy method that returns an empty query"""
        return models.Q()
