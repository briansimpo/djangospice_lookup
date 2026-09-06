from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias

from django.db import models

from .dependencies import (
    LookupDependency,
    LookupDependencyDeclaration,
    LookupDependencyResolver,
)
from .exceptions import LookupConfigurationError
from .scope import LookupScope, UserScope
from .identifier import LookupIdentifier


LookupSearchField: TypeAlias = str


@dataclass(frozen=True, slots=True)
class LookupDefinition:
    """
    Declarative definition of a model lookup.
    """

    model: type[models.Model]

    depends_on: (
        LookupDependencyDeclaration
        | Iterable[LookupDependencyDeclaration]
        | None
    ) = None

    search_fields: tuple[str, ...] = ()

    ordering: tuple[str, ...] = ()

    label_field: str | None = None

    description_field: str | None = None

    page_size: int = 20

    max_page_size: int = 100

    scope: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.model, type) or not issubclass(
            self.model,
            models.Model,
        ):
            raise LookupConfigurationError(
                "LookupDefinition.model must be a Django model class."
            )

        if self.page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.page_size must be greater than zero."
            )

        if self.max_page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.max_page_size must be greater than zero."
            )

        if self.page_size > self.max_page_size:
            raise LookupConfigurationError(
                "page_size cannot exceed max_page_size."
            )

        if self.scope is not None:
            if not isinstance(self.scope, str):
                raise LookupConfigurationError(
                    "LookupDefinition.scope must be a string."
                )

            if not self.scope.strip():
                raise LookupConfigurationError(
                    "LookupDefinition.scope cannot be empty."
                )

    @property
    def identifier(self) -> LookupIdentifier:
        return LookupIdentifier.from_model(self.model)

    @property
    def app_name(self) -> str:
        return self.identifier.app_name


    @property
    def name(self) -> str:
        return self.identifier.name


    @property
    def key(self) -> tuple[str, str]:
        return self.identifier.key

    @property
    def dependencies(self) -> tuple[LookupDependency, ...]:
        return LookupDependencyResolver.normalize(
            self.model,
            self.depends_on,
        )

    @property
    def dependency_paths(self) -> tuple[str, ...]:
        return tuple(
            dependency.path
            for dependency in self.dependencies
        )

    @property
    def lookup_scope(self) -> LookupScope | None:
        if self.scope is None:
            return None

        return UserScope(self.scope.strip())