from __future__ import annotations

import jwt

from dataclasses import dataclass
from typing import Any, Protocol

from django.core import signing
from django.http import HttpRequest
from django.contrib.auth import get_user_model

from .conf import LookupConfig, lookup_config
from .exceptions import AuthenticationError, AuthenticationRequired
from .identifier import LookupIdentifier

user_model = get_user_model()


@dataclass(frozen=True, slots=True)
class LookupSecurityContext:
    user: Any | None = None
    authentication: str = "unknown"
    authenticated: bool = False
    lookup: LookupIdentifier | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.authenticated

    @property
    def is_session(self) -> bool:
        return self.authentication == "session"

    @property
    def is_token(self) -> bool:
        return self.authentication == "token"

    @property
    def is_widget(self) -> bool:
        return self.authentication == "widget"


class Authenticator(Protocol):
    def authenticate(self, request: HttpRequest, lookup: LookupIdentifier) -> LookupSecurityContext | None:
        ...


class SessionAuthenticator:
    def authenticate(self, request: HttpRequest, lookup: LookupIdentifier) -> LookupSecurityContext | None:
        user = getattr(request, "user", None)

        if user is None:
            return None

        if not getattr(
            user,
            "is_authenticated",
            False,
        ):
            return None

        return LookupSecurityContext(
            user=user,
            authentication="session",
            authenticated=True,
            lookup=lookup,
        )


class JWTBearerTokenAuthenticator:
    """
    Authenticate JWT bearer tokens.
    """

    scheme = "Bearer"

    def __init__(self, *, config: LookupConfig = lookup_config) -> None:
        self.config = config

    def authenticate(self, request: HttpRequest, lookup: LookupIdentifier) -> LookupSecurityContext | None:
        authorization = request.headers.get(
            "Authorization",
            "",
        ).strip()

        if not authorization:
            return None

        scheme, separator, token = authorization.partition(" ")

        if (
            not separator
            or scheme.casefold() != self.scheme.casefold()
            or not token.strip()
        ):
            return None

        try:
            payload = jwt.decode(
                token.strip(),
                self.config.jwt_secret_key,
                algorithms=list(
                    self.config.jwt_algorithms,
                ),
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(
                "Bearer token has expired."
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(
                "Invalid bearer token."
            ) from exc

        if not isinstance(payload, dict):
            raise AuthenticationError(
                "Invalid bearer token payload."
            )

        subject = payload.get(
            self.config.jwt_user_claim,
        )

        if subject is None:
            raise AuthenticationError(
                "Bearer token is missing the "
                f"'{self.config.jwt_user_claim}' claim."
            )

        user = self.resolve_user(
            subject,
            request,
            lookup,
        )

        if user is None:
            raise AuthenticationError(
                "Bearer token subject could not be resolved."
            )

        return LookupSecurityContext(
            user=user,
            authentication="token",
            authenticated=True,
            lookup=lookup,
        )

    def resolve_user(self, subject: Any, request: HttpRequest, lookup: LookupIdentifier ) -> Any | None:
        if self.config.jwt_user_resolver is not None:
            return self.config.jwt_user_resolver(
                subject,
                request,
                lookup,
            )

        try:
            return user_model._default_manager.get(
                pk=subject,
            )
        except user_model.DoesNotExist:
            return None


class WidgetCapabilityAuthenticator:
    """
    Authenticate short-lived signed widget capabilities.
    """

    def __init__(self, *, config: LookupConfig = lookup_config) -> None:
        self.config = config

    def issue(self, lookup: LookupIdentifier, *, subject: Any = None) -> str:
        return signing.dumps(
            {
                "lookup": str(lookup),
                "subject": subject,
            },
            salt=self.config.widget_token_salt,
            compress=True,
        )

    def authenticate(self, request: HttpRequest, lookup: LookupIdentifier) -> LookupSecurityContext | None:
        token = request.headers.get(
            self.config.widget_token_header,
            "",
        ).strip()

        if not token:
            return None

        try:
            payload = signing.loads(
                token,
                salt=self.config.widget_token_salt,
                max_age=self.config.widget_token_max_age,
            )
        except signing.BadSignature as exc:
            raise AuthenticationError(
                "Invalid widget capability."
            ) from exc

        if not isinstance(payload, dict):
            raise AuthenticationError(
                "Invalid widget capability."
            )

        if payload.get("lookup") != str(lookup):
            raise AuthenticationError(
                "Widget capability is not valid "
                "for this lookup."
            )

        return LookupSecurityContext(
            user=payload.get("subject"),
            authentication="widget",
            authenticated=True,
            lookup=lookup,
        )


class LookupSecurity:
    """
    Coordinates lookup authentication.
    """

    def __init__(self, authenticators: tuple[Authenticator, ...], *, require_authentication: bool = True) -> None:
        if (
            not authenticators
            and require_authentication
        ):
            raise ValueError(
                "At least one authenticator is required."
            )

        self.authenticators = authenticators
        self.require_authentication = (
            require_authentication
        )

    @classmethod
    def defaults(cls, *, config: LookupConfig = lookup_config) -> "LookupSecurity":
        return cls(
            authenticators=(
                WidgetCapabilityAuthenticator(config=config),
                SessionAuthenticator(),
                JWTBearerTokenAuthenticator(config=config),
            ),
            require_authentication=(
                config.require_authentication
            ),
        )

    def authenticate(self, request: HttpRequest, lookup: LookupIdentifier) -> LookupSecurityContext:
        for authenticator in self.authenticators:
            context = authenticator.authenticate(
                request,
                lookup,
            )

            if context is not None:
                return context

        if self.require_authentication:
            raise AuthenticationRequired(
                "Authentication is required."
            )

        return LookupSecurityContext(
            authenticated=False,
            lookup=lookup,
        )