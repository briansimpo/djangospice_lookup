from __future__ import annotations

from django.http import JsonResponse

from .exceptions import (
    LookupError,
    LookupConfigurationError,
    AuthenticationError,
    AuthenticationRequired,
)


def lookup_exception_handler(exc: Exception) -> JsonResponse | None:

    if isinstance(exc, AuthenticationRequired,):
        return JsonResponse(
            {
                "detail": str(exc),
                "code": "authentication_required",
            },
            status=401,
        )

    if isinstance(exc, AuthenticationError):
        return JsonResponse(
            {
                "detail": str(exc),
                "code": "authentication_failed",
            },
            status=401,
        )

    if isinstance(exc, LookupError):
        return JsonResponse(
            {
                "detail": str(exc),
                "code": "invalid_request",
            },
            status=400,
        )

    if isinstance(exc, LookupConfigurationError):
        return JsonResponse(
            {
                "detail": str(exc),
                "code": "lookup_configuration_error",
            },
            status=404,
        )

    return None