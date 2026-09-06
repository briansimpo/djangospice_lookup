from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .exceptions import (
    AmbiguousLookupDependency,
    InvalidLookupDependency,
    InvalidLookupField,
)


LookupDependencyDeclaration: TypeAlias = (
    str | type[models.Model]
)


@dataclass(frozen=True, slots=True)
class LookupDependency:
    """
    Normalized lookup dependency.

    A dependency is either declared explicitly using a
    relationship path or implicitly using a related model.
    """

    path: str
    model: type[models.Model] | None = None

    @property
    def name(self) -> str:
        return self.path


class RelationResolver:
    """
    Resolve Django model relationships.
    """

    @classmethod
    def resolve_path(cls, source_model: type[models.Model], path: str) -> tuple[models.Field, ...]:
        """
        Resolve a relationship path.
        """

        if not path:
            raise InvalidLookupField(
                "Lookup dependency path cannot be empty."
            )

        current_model = source_model
        fields: list[models.Field] = []

        for part in path.split("__"):
            try:
                field = current_model._meta.get_field(part)
            except FieldDoesNotExist as exc:
                raise InvalidLookupField(
                    f"'{path}' is not a valid relationship path "
                    f"on '{source_model._meta.label}'."
                ) from exc

            if not field.is_relation:
                raise InvalidLookupField(
                    f"'{path}' is not a relationship path. "
                    f"'{part}' on "
                    f"'{current_model._meta.label}' "
                    "is not relational."
                )

            related_model = field.related_model

            if related_model is None:
                raise InvalidLookupField(
                    f"Relationship '{part}' on "
                    f"'{current_model._meta.label}' has no "
                    "related model."
                )

            fields.append(field)
            current_model = related_model

        return tuple(fields)

    @classmethod
    def find_relation_to_model(cls, source_model: type[models.Model], related_model: type[models.Model]) -> models.Field:
        """
        Find a direct relationship from source_model to
        related_model.
        """

        matches: list[models.Field] = []

        for field in source_model._meta.get_fields():
            if not field.is_relation:
                continue

            if field.related_model is not related_model:
                continue

            # Reverse relations are not suitable for the
            # convention-based dependency API.
            if not field.concrete:
                continue

            matches.append(field)

        if not matches:
            raise InvalidLookupDependency(
                f"'{source_model._meta.label}' has no direct "
                f"relationship to '{related_model._meta.label}'."
            )

        if len(matches) > 1:
            raise AmbiguousLookupDependency(
                f"'{source_model._meta.label}' has multiple "
                f"relationships to '{related_model._meta.label}'. "
                "Specify the relationship path explicitly."
            )

        return matches[0]


class LookupDependencyResolver:
    """
    Convert a depends_on declaration into normalized
    LookupDependency instances.
    """

    @classmethod
    def normalize(cls, source_model: type[models.Model],
        depends_on: (
            LookupDependencyDeclaration
            | Iterable[LookupDependencyDeclaration]
            | None
        ),
    ) -> tuple[LookupDependency, ...]:

        declarations = cls._normalize_input(
            depends_on
        )

        dependencies: list[LookupDependency] = []

        for declaration in declarations:

            if isinstance(declaration, str):
                RelationResolver.resolve_path(
                    source_model,
                    declaration,
                )

                dependencies.append(
                    LookupDependency(
                        path=declaration,
                    )
                )

                continue

            if cls.is_model(declaration):
                field = RelationResolver.find_relation_to_model(
                    source_model,
                    declaration,
                )

                dependencies.append(
                    LookupDependency(
                        path=field.name,
                        model=declaration,
                    )
                )

                continue

            raise InvalidLookupDependency(
                "Each depends_on item must be either a "
                "relationship path string or Django model class."
            )

        return cls._deduplicate(
            dependencies
        )

    @staticmethod
    def is_model(value: object) -> bool:
        return (
            isinstance(value, type)
            and issubclass(value, models.Model)
        )

    @staticmethod
    def _normalize_input(depends_on) -> tuple[LookupDependencyDeclaration, ...]:

        if depends_on is None:
            return ()

        if isinstance(depends_on, str):
            return (depends_on,)

        if LookupDependencyResolver.is_model(
            depends_on
        ):
            return (depends_on,)

        try:
            return tuple(depends_on)
        except TypeError as exc:
            raise InvalidLookupDependency(
                "depends_on must be a relationship path, "
                "Django model, or iterable of either."
            ) from exc

    @staticmethod
    def _deduplicate(dependencies: list[LookupDependency]) -> tuple[LookupDependency, ...]:

        result: list[LookupDependency] = []
        seen: set[str] = set()

        for dependency in dependencies:
            if dependency.path in seen:
                continue

            seen.add(dependency.path)
            result.append(dependency)

        return tuple(result)