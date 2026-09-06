from __future__ import annotations

from .definition import LookupDefinition
from .registry import LookupRegistry


class LookupDefinitionResolver:
    """
    Resolves registered lookup definitions.
    """

    def __init__(self, registry: LookupRegistry) -> None:
        self.registry = registry

    def resolve(self,app_name: str, name: str) -> LookupDefinition:
        return self.registry.get(
            app_name,
            name,
        )