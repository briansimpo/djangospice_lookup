from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .conf import LookupConfig, lookup_config
from .definition import LookupDefinition
from .engine import LookupEngine
from .query import LookupQuery
from .result import LookupResult
from .security import LookupSecurityContext
from .helpers import get_dependencies, positive_int




class LookupAdapter:
    """
    HTTP adapter for the lookup engine.

    Converts an HTTP GET request into a LookupQuery and
    returns a LookupResult.

    The adapter does not perform lookup logic or ORM operations.
    """

    def __init__(self,*, engine: LookupEngine, config: LookupConfig = lookup_config) -> None:
        self.engine = engine
        self.config = config

    def build_query(self, request: HttpRequest, definition: LookupDefinition, *, security: LookupSecurityContext | None = None) -> LookupQuery:

        search = request.GET.get(
            self.config.search_param,
            "",
        ).strip()

        page = positive_int(
            request.GET.get(
                self.config.page_param,
            ),
            default=self.config.page,
        )

        page_size = positive_int(
            request.GET.get(
                self.config.page_size_param,
            ),
            default=self.config.page_size,
        )

        page_size = min(
            page_size,
            definition.max_page_size,
            self.config.max_page_size,
        )

        dependencies = get_dependencies(
            request,
            definition,
        )

        return LookupQuery(
            model=definition.model,
            definition=definition,
            search=search,
            page=page,
            page_size=page_size,
            dependencies=dependencies,
            security=security,
        )

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, request: HttpRequest, definition: LookupDefinition) -> LookupResult:
        """
        Execute a lookup request and return its HTTP response.
        """

        query = self.build_query(request, definition)

        result = self.engine.execute(query)

        return result

