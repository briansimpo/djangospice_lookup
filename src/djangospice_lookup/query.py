from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .security import LookupSecurityContext
from .definition import LookupDefinition


@dataclass(frozen=True, slots=True)
class LookupQuery:
    """
    Runtime lookup request.

    The definition describes what the lookup supports.

    This object contains the current values supplied by the
    caller/request.
    """

    definition: LookupDefinition

    search: str = ""

    dependencies: Mapping[str, Any] = field(default_factory=dict)

    page: int = 1

    page_size: int | None = None

    security: LookupSecurityContext | None = None

    def get_page_size(self) -> int:
        if self.page_size is None:
            return self.definition.page_size

        return min(
            max(self.page_size, 1),
            self.definition.max_page_size,
        )

    @property
    def model(self):
        return self.definition.model