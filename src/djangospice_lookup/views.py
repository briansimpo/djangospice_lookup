from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views import View

from .engine import LookupEngine
from .adapter import LookupAdapter
from .security import LookupSecurity
from .resolver import LookupDefinitionResolver
from .identifier import LookupIdentifier
from .registry import lookup_registry


class LookupView(View):
    """
    Generic HTTP endpoint for model lookups.

    The view is responsible only for Django request handling and
    resolving the model/lookup definition. HTTP parsing and lookup
    execution are delegated to their respective services.

    Example:

        /lookup/academic/course/

    Search:

        /lookup/academic/course/?q=computer

    Cascading:

        /lookup/academic/course/?program=<uuid>

    Multiple cascading dependencies:

        /lookup/academic/course/
            ?program=<uuid>
            &program__department=<uuid>
    """

    engine = LookupEngine()

    adapter = LookupAdapter(engine=engine)

    definition_resolver = LookupDefinitionResolver(registry=lookup_registry)

    security = LookupSecurity.defaults()

    def get(self, request: HttpRequest, app_name: str, name: str) -> JsonResponse:
        
        identifier = LookupIdentifier(
            app_name,
            name,
        )

        security = self.security.authenticate(
            request,
            identifier,
        )

        definition = self.definition_resolver.resolve(
            identifier.app_name,
            identifier.name,
        )

        result = self.adapter.execute(
            request,
            definition,
            security=security,
        )

        return JsonResponse(
            result.as_dict(),
        )