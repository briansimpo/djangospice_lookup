# djangospice/ui/widgets/lookup.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django import forms
from django.db import models
from django.urls import reverse

from .conf import LookupConfig, lookup_config
from .definition import LookupDefinition
from .dependencies import LookupDependencyResolver
from .identifier import LookupIdentifier
from .apps import namespace


class LookupWidget(forms.Select):
    """
    Django Select widget backed by a Djangospice lookup endpoint.

    The widget remains a standard Django form widget and therefore
    works with Django's normal form fields, including:

        ModelChoiceField
        ModelMultipleChoiceField
        ChoiceField
        TypedChoiceField

    It can also be used with django-filter.

    A lookup can be configured using either a registered model or
    an existing LookupDefinition.

    Example:

        course = forms.ModelChoiceField(
            queryset=Course.objects.all(),
            widget=LookupWidget(
                model=Course,
            ),
        )

    With a lookup definition:

        course = forms.ModelChoiceField(
            queryset=Course.objects.all(),
            widget=LookupWidget(
                definition=course_lookup,
            ),
        )

    Cascading lookups:

        course = forms.ModelChoiceField(
            queryset=Course.objects.all(),
            widget=LookupWidget(
                model=Course,
                depends_on=(
                    "program",
                    "program__department",
                ),
            ),
        )
    """

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
        choices: Iterable | None = (),
        *,
        model: type[models.Model] | None = None,
        definition: LookupDefinition | None = None,
        depends_on: (
            str
            | type[models.Model]
            | Iterable[str | type[models.Model]]
            | None
        ) = None,
        placeholder: str = "Select...",
        search_placeholder: str = "Search...",
        page_size: int | None = None,
        min_search_length: int = 0,
        allow_clear: bool = True,
        url: str | None = None,
        multi_select: bool | None = None,
        token: str | None = None,
        config: LookupConfig = lookup_config,
        **kwargs: Any,
    ) -> None:
        model = self.resolve_model(
            model=model,
            definition=definition,
        )

        dependencies = self.resolve_dependencies(
            definition=definition,
            depends_on=depends_on,
        )

        self.model = model
        self.definition = definition
        self.token = token
        self.config = config

        self.depends_on = self.normalize_depends_on(
            dependencies,
        )

        self.dependencies = (
            LookupDependencyResolver.normalize(
                model,
                self.depends_on,
            )
        )

        self.placeholder = placeholder
        self.search_placeholder = search_placeholder

        self.page_size = self.validate_page_size(
            page_size
            if page_size is not None
            else config.page_size,
        )

        self.min_search_length = (
            self.validate_min_search_length(
                min_search_length,
            )
        )

        self.allow_clear = allow_clear
        self.multi_select = multi_select

        self.lookup_url = (
            url
            if url is not None
            else self.get_lookup_url()
        )

        super().__init__(
            attrs=attrs,
            choices=choices,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_model(
        *,
        model: type[models.Model] | None,
        definition: LookupDefinition | None,
    ) -> type[models.Model]:
        if definition is not None:
            if (
                model is not None
                and model is not definition.model
            ):
                raise ValueError(
                    "model and definition.model must refer "
                    "to the same model."
                )

            return definition.model

        if model is None:
            raise ValueError(
                "LookupWidget requires either "
                "model or definition."
            )

        if not isinstance(model, type) or not issubclass(
            model,
            models.Model,
        ):
            raise TypeError(
                "model must be a Django model class."
            )

        return model

    @staticmethod
    def resolve_dependencies(
        *,
        definition: LookupDefinition | None,
        depends_on,
    ):
        if depends_on is not None:
            return depends_on

        if definition is not None:
            return definition.depends_on

        return ()

    @staticmethod
    def normalize_depends_on(
        depends_on,
    ) -> tuple[
        str | type[models.Model],
        ...,
    ]:
        if depends_on is None:
            return ()

        if isinstance(
            depends_on,
            (str, type),
        ):
            return (depends_on,)

        return tuple(depends_on)

    @staticmethod
    def validate_page_size(
        page_size: int,
    ) -> int:
        if page_size <= 0:
            raise ValueError(
                "page_size must be greater than zero."
            )

        return page_size

    @staticmethod
    def validate_min_search_length(
        value: int,
    ) -> int:
        if value < 0:
            raise ValueError(
                "min_search_length cannot be negative."
            )

        return value

    @property
    def identifier(self) -> LookupIdentifier:
        return LookupIdentifier.from_model(
            self.model,
        )

    def get_lookup_url(self) -> str:
        return reverse(
           namespace,
            kwargs={
                "app_name": self.identifier.app_name,
                "name": self.identifier.name,
            },
        )

    # ------------------------------------------------------------------
    # Select behaviour
    # ------------------------------------------------------------------

    def use_required_attribute(
        self,
        initial,
    ) -> bool:
        """
        Preserve Django's normal Select behaviour.
        """
        return super().use_required_attribute(
            initial,
        )

    def format_value(
        self,
        value,
    ):
        """
        Preserve Django's normal value handling.

        This is important for:

        - ModelChoiceField
        - ModelMultipleChoiceField
        - initial values
        - bound forms
        """
        return super().format_value(value)

    # ------------------------------------------------------------------
    # Lookup metadata
    # ------------------------------------------------------------------

    def get_lookup_dependencies(self) -> tuple[str, ...]:
        return tuple(
            dependency.path
            for dependency in self.dependencies
        )

    def get_client_config(self, *, name: str) -> dict[str, Any]:
        """
        Return the client-side configuration for this lookup widget.
        """
        if multi_select is None:
            multi_select = self.multi_select

        return {
            "type": "lookup",
            "name": name,
            "url": self.lookup_url,
            "search_param": self.config.search_param,
            "page_param": self.config.page_param,
            "page_size_param": self.config.page_size_param,
            "page_size": self.page_size,
            "min_search_length": self.min_search_length,
            "placeholder": self.placeholder,
            "search_placeholder": self.search_placeholder,
            "allow_clear": self.allow_clear,
            "multi_select": self.multi_select,
            "dependencies": self.get_lookup_dependencies(),
        }

    # ------------------------------------------------------------------
    # HTML attributes
    # ------------------------------------------------------------------

    def build_attrs(
        self,
        base_attrs: dict[str, Any] | None = None,
        extra_attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        attrs = super().build_attrs(
            base_attrs,
            extra_attrs,
        )

        attrs.update(
            {
                "data-djangospice-lookup": "",
                "data-lookup-url": self.lookup_url,

                "data-lookup-search-param": (
                    self.config.search_param
                ),

                "data-lookup-page-param": (
                    self.config.page_param
                ),

                "data-lookup-page-size-param": (
                    self.config.page_size_param
                ),

                "data-lookup-page-size": str(
                    self.page_size,
                ),

                "data-lookup-min-search-length": str(
                    self.min_search_length,
                ),

                "data-lookup-placeholder": (
                    self.placeholder
                ),

                "data-lookup-search-placeholder": (
                    self.search_placeholder
                ),

                "data-lookup-allow-clear": (
                    "true"
                    if self.allow_clear
                    else "false"
                ),
            }
        )

        if self.token:
            attrs["data-lookup-token"] = self.token

        dependencies = self.get_lookup_dependencies()

        if dependencies:
            attrs["data-lookup-dependencies"] = ",".join(
                dependencies,
            )

        return attrs

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def get_context(
        self,
        name: str,
        value,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        context = super().get_context(
            name,
            value,
            attrs,
        )

        widget = context["widget"]

        # Canonical field name used by lookup.js to resolve
        # dependency fields in the current form.
        widget["attrs"]["data-lookup-name"] = name

        widget["lookup"] = {
            "url": self.lookup_url,
            "dependencies": self.dependencies,
            "dependency_paths": self.get_lookup_dependencies(),
            "placeholder": self.placeholder,
            "search_placeholder": self.search_placeholder,
            "page_size": self.page_size,
            "min_search_length": self.min_search_length,
            "allow_clear": self.allow_clear,
            "multi_select": self.multi_select,
        }

        return context