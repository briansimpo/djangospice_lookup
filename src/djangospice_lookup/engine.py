from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.db.models import Q, QuerySet

from .dependencies import RelationResolver
from .exceptions import (
    InvalidLookupDependency,
    InvalidLookupOrdering,
    InvalidLookupQuery,
)
from .query import LookupQuery
from .result import LookupOption, LookupResult
from .search import validate_search_fields


class LookupEngine:
    """
    Execute LookupQuery instances against Django models.
    """

    def execute(self, query: LookupQuery) -> LookupResult:

        self.validate_query(
            query
        )

        queryset = self.get_queryset(
            query
        )

        queryset = self.apply_dependencies(
            queryset,
            query,
        )

        queryset = self.apply_search(
            queryset,
            query,
        )

        queryset = self.apply_ordering(
            queryset,
            query,
        )

        return self.paginate(
            queryset,
            query,
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def validate_query(self, query: LookupQuery) -> None:

        if not isinstance(
            query,
            LookupQuery,
        ):
            raise InvalidLookupQuery(
                "LookupEngine.execute() expects a LookupQuery."
            )

        if query.page < 1:
            raise InvalidLookupQuery(
                "Lookup page must be greater than zero."
            )

        if query.page_size is not None:
            if query.page_size < 1:
                raise InvalidLookupQuery(
                    "Lookup page size must be greater "
                    "than zero."
                )

            if (
                query.page_size
                > query.definition.max_page_size
            ):
                raise InvalidLookupQuery(
                    "Lookup page size exceeds the "
                    "configured maximum."
                )

        self.validate_dependencies(
            query
        )

        self.validate_search(
            query
        )

        self.validate_ordering(
            query
        )

    # ---------------------------------------------------------
    # QuerySet
    # ---------------------------------------------------------

    def get_queryset(self, query: LookupQuery) -> QuerySet:
        return query.model._default_manager.all()

    # ---------------------------------------------------------
    # Dependencies
    # ---------------------------------------------------------

    def validate_dependencies(self, query: LookupQuery) -> None:

        declared = {
            dependency.path
            for dependency in query.definition.dependencies
        }

        supplied = set(
            query.dependencies
        )

        undeclared = supplied - declared

        if undeclared:
            paths = ", ".join(
                sorted(undeclared)
            )

            raise InvalidLookupDependency(
                f"Undeclared lookup dependencies: {paths}."
            )

        for dependency in query.definition.dependencies:

            RelationResolver.resolve_path(
                query.model,
                dependency.path,
            )

    def apply_dependencies(self, queryset: QuerySet, query: LookupQuery) -> QuerySet:

        for dependency in query.definition.dependencies:

            if dependency.path not in query.dependencies:
                continue

            value = query.dependencies[
                dependency.path
            ]

            if self.is_empty_dependency(
                value
            ):
                continue

            queryset = self.apply_dependency(
                queryset,
                dependency.path,
                value,
            )

        return queryset

    def apply_dependency(self, queryset: QuerySet, path: str, value: Any) -> QuerySet:

        RelationResolver.resolve_path(
            queryset.model,
            path,
        )

        return queryset.filter(
            **{
                path: value,
            }
        )

    def apply_scope(self, queryset: QuerySet, query: LookupQuery) -> QuerySet:

        scope = query.definition.lookup_scope

        if scope is None:
            return queryset

        security = query.security

        if security is None:
            return queryset.none()

        return scope.apply(queryset, security)

    @staticmethod
    def is_empty_dependency(value: Any) -> bool:

        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
                frozenset,
                dict,
            ),
        ):
            return not value

        return False

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def validate_search(self, query: LookupQuery) -> None:

        validate_search_fields(
            query.model,
            query.definition.search_fields,
        )

    def apply_search(self, queryset: QuerySet, query: LookupQuery) -> QuerySet:

        search = query.search.strip()

        if not search:
            return queryset

        fields = validate_search_fields(
            query.model,
            query.definition.search_fields,
        )

        if not fields:
            return queryset.none()

        condition = Q()

        for field in fields:
            condition |= Q(
                **{
                    f"{field}__icontains": search,
                }
            )

        return queryset.filter(
            condition
        )

    # ---------------------------------------------------------
    # Ordering
    # ---------------------------------------------------------

    def validate_ordering(self, query: LookupQuery) -> None:

        for ordering in query.definition.ordering:

            field_path = ordering.lstrip("-")

            if not field_path:
                raise InvalidLookupOrdering(
                    "Ordering field cannot be empty."
                )

            self.validate_ordering_path(
                query.model,
                field_path,
            )

    def validate_ordering_path(self, model, path: str) -> None:

        current_model = model

        for index, part in enumerate(path.split("__") ):

            try:
                field = current_model._meta.get_field(
                    part
                )
            except Exception as exc:
                raise InvalidLookupOrdering(
                    f"'{path}' is not a valid ordering "
                    f"path on '{model._meta.label}'."
                ) from exc

            is_last = (
                index == len(path.split("__")) - 1
            )

            if field.is_relation:

                if is_last:
                    raise InvalidLookupOrdering(
                        f"Ordering path '{path}' ends on "
                        "a relationship."
                    )

                current_model = field.related_model

    def apply_ordering(self, queryset: QuerySet, query: LookupQuery) -> QuerySet:

        ordering = query.definition.ordering

        if ordering:
            return queryset.order_by(
                *ordering
            )

        return queryset.order_by(
            queryset.model._meta.pk.name
        )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    def paginate(self, queryset: QuerySet, query: LookupQuery) -> LookupResult:

        page_size = query.get_page_size()

        paginator = Paginator(
            queryset,
            page_size,
        )

        page = paginator.get_page(
            query.page
        )

        return LookupResult(
            options=tuple(
                self.to_option(obj)
                for obj in page.object_list
            ),
            page=page.number,
            page_size=page_size,
            total=paginator.count,
            has_next=page.has_next(),
            has_previous=page.has_previous(),
        )

    # ---------------------------------------------------------
    # Option conversion
    # ---------------------------------------------------------

    def to_option(self, obj) -> LookupOption:

        return LookupOption(
            value=str(obj.pk),
            label=self.get_label(obj),
            description=self.get_description(obj),
            object=obj,
        )

    def get_label(self, obj) -> str:
        return str(obj)

    def get_description(self, obj) -> str | None:
        return None