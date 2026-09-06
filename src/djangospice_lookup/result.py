from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LookupOption:
    """
    One selectable lookup option.
    """

    value: str
    label: str
    description: str | None = None
    object: Any = None

    def as_dict(self, *, include_object: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "value": self.value,
            "label": self.label,
            "description": self.description,
        }

        if include_object:
            data["object"] = self.object

        return data


@dataclass(frozen=True, slots=True)
class LookupResult:
    """
    Result returned by LookupEngine.
    """

    options: tuple[LookupOption, ...]

    page: int
    page_size: int
    total: int

    has_next: bool
    has_previous: bool

    @property
    def is_empty(self) -> bool:
        return not self.options

    @property
    def pages(self) -> int:
        if self.page_size <= 0:
            return 0

        return (
            self.total + self.page_size - 1
        ) // self.page_size

    def as_dict(self, *, include_objects: bool = False) -> dict[str, Any]:
        return {
            "results": [
                option.as_dict(
                    include_object=include_objects,
                )
                for option in self.options
            ],
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "pages": self.pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
            },
        }