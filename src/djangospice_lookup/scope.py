from __future__ import annotations

from typing import Protocol

from django.db.models import QuerySet

from .security import LookupSecurityContext


class LookupScope(Protocol):
    """
    Restricts the queryset according to the security context.
    """

    def apply(self, queryset: QuerySet, security: LookupSecurityContext) -> QuerySet:
        ...


class UserScope:
    """
    Restrict records through an arbitrary Django relationship path.

    """

    def __init__(self, path: str) -> None:
        if not path or not path.strip():
            raise ValueError("Scope path cannot be empty.")

        self.path = path.strip()

    def apply(self, queryset: QuerySet, security: LookupSecurityContext) -> QuerySet:

        user = security.user

        if user is None:
            return queryset.none()

        return queryset.filter(
            **{self.path: user}
        )