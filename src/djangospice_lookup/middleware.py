from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .handlers import lookup_exception_handler


class LookupExceptionMiddleware:
    def __init__(
        self,
        get_response: Callable[
            [HttpRequest],
            HttpResponse,
        ],
    ) -> None:
        self.get_response = get_response

    def __call__(
        self,
        request: HttpRequest,
    ) -> HttpResponse:

        try:
            return self.get_response(request)

        except Exception as exc:
            response = lookup_exception_handler(exc)

            if response is not None:
                return response

            raise