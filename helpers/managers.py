from __future__ import annotations
from typing import Any, Optional, TypeVar, Union, List, Generic
from django.db import models
from django.core.exceptions import ImproperlyConfigured


M = TypeVar("M", bound=models.Model)


class SearchableQuerySet(models.QuerySet[M]):
    """A model queryset that supports search"""

    model: M

    def search(self, query: Union[str, Any], fields: Union[List[str], str]):
        """
        Search the queryset for the given query in the given fields.

        :param query: The search query.
        :param fields: The names of the model fields to search in. Can be a traversal path.
        :return: A queryset containing the search results.
        """
        if isinstance(fields, str):
            fields = [
                fields,
            ]

        fields = fields or []
        query = query.strip()
        if not query:
            return self.none()

        q = models.Q()
        for field in fields:
            q |= models.Q(**{f"{field.replace(".", "__")}__icontains": query})
        return self.filter(q).distinct()


SQ = TypeVar("SQ", bound=SearchableQuerySet)


class BaseSearchableManager(Generic[SQ], models.manager.BaseManager):
    """Base model manager that supports search"""

    def __init__(self) -> None:
        super().__init__()
        if not issubclass(self._queryset_class, SearchableQuerySet):
            raise ImproperlyConfigured(
                f"`_queryset_class` must be an instance of {SearchableQuerySet.__name__}"
            )

    def get_queryset(self) -> SQ:
        return super().get_queryset()

    def search(
        self, query: Union[str, Any], fields: Optional[Union[List[str], str]] = None
    ) -> SQ:
        """
        Search the model for the given query in the given fields.

        :param query: The search query.
        :param fields: The names of the model fields to search in. Can be a traversal path.
        :return: A queryset containing the search results.
        """
        return self.get_queryset().search(query=query, fields=fields)
