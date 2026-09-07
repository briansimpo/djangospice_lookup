from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from django.conf import settings

from .utils import algorithms, setting, non_empty_string, positive_int, resolve_callable


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_SEARCH_PARAM = "q"
DEFAULT_PAGE_PARAM = "page"
DEFAULT_PAGE_SIZE_PARAM = "page_size"

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGE_SIZE = 100

DEFAULT_JWT_ALGORITHMS = (
    "HS256",
)
DEFAULT_JWT_USER_CLAIM = "user_id"

DEFAULT_WIDGET_TOKEN_HEADER = "X-Lookup-Token"
DEFAULT_WIDGET_TOKEN_SALT = "djangospice_lookup.widget"
DEFAULT_WIDGET_TOKEN_MAX_AGE = 300

DEFAULT_REQUIRE_AUTHENTICATION = True


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LookupConfig:
    """
    Resolved configuration for djangospice_lookup.

    Values are resolved once from package defaults and Django settings.
    """

    # Request
    search_param: str
    page_param: str
    page_size_param: str

    # Pagination
    page: int
    page_size: int
    max_page_size: int

    # JWT
    jwt_secret_key: str
    jwt_algorithms: tuple[str, ...]
    jwt_user_claim: str
    jwt_user_resolver: Any | None

    # Widget capability
    widget_token_header: str
    widget_token_salt: str
    widget_token_max_age: int

    # Security
    require_authentication: bool


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def get_lookup_config() -> LookupConfig:
    """
    Resolve and validate djangospice_lookup configuration.

    Precedence:

        Django setting
            ↓
        package default
    """

    search_param = non_empty_string(
        "DJANGOSPICE_LOOKUP_SEARCH_PARAM",
        setting(
            "DJANGOSPICE_LOOKUP_SEARCH_PARAM",
            DEFAULT_SEARCH_PARAM,
        ),
    )

    page_param = non_empty_string(
        "DJANGOSPICE_LOOKUP_PAGE_PARAM",
        setting(
            "DJANGOSPICE_LOOKUP_PAGE_PARAM",
            DEFAULT_PAGE_PARAM,
        ),
    )

    page_size_param = non_empty_string(
        "DJANGOSPICE_LOOKUP_PAGE_SIZE_PARAM",
        setting(
            "DJANGOSPICE_LOOKUP_PAGE_SIZE_PARAM",
            DEFAULT_PAGE_SIZE_PARAM,
        ),
    )

    page = positive_int(
        "DJANGOSPICE_LOOKUP_PAGE",
        setting(
            "DJANGOSPICE_LOOKUP_PAGE",
            DEFAULT_PAGE,
        ),
    )

    page_size = positive_int(
        "DJANGOSPICE_LOOKUP_PAGE_SIZE",
        setting(
            "DJANGOSPICE_LOOKUP_PAGE_SIZE",
            DEFAULT_PAGE_SIZE,
        ),
    )

    max_page_size = positive_int(
        "DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE",
        setting(
            "DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE",
            DEFAULT_MAX_PAGE_SIZE,
        ),
    )

    if page_size > max_page_size:
        raise ValueError(
            "DJANGOSPICE_LOOKUP_PAGE_SIZE cannot be "
            "greater than DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE."
        )

    jwt_secret_key = non_empty_string(
        "DJANGOSPICE_LOOKUP_JWT_SECRET_KEY",
        setting(
            "DJANGOSPICE_LOOKUP_JWT_SECRET_KEY",
            settings.SECRET_KEY,
        ),
    )

    jwt_algorithms = algorithms(
        setting(
            "DJANGOSPICE_LOOKUP_JWT_ALGORITHMS",
            DEFAULT_JWT_ALGORITHMS,
        ),
    )

    jwt_user_claim = non_empty_string(
        "DJANGOSPICE_LOOKUP_JWT_USER_CLAIM",
        setting(
            "DJANGOSPICE_LOOKUP_JWT_USER_CLAIM",
            DEFAULT_JWT_USER_CLAIM,
        ),
    )

    jwt_user_resolver = resolve_callable(
        setting(
            "DJANGOSPICE_LOOKUP_JWT_USER_RESOLVER",
            None,
        ),
    )

    widget_token_header = non_empty_string(
        "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_HEADER",
        setting(
            "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_HEADER",
            DEFAULT_WIDGET_TOKEN_HEADER,
        ),
    )

    widget_token_salt = non_empty_string(
        "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_SALT",
        setting(
            "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_SALT",
            DEFAULT_WIDGET_TOKEN_SALT,
        ),
    )

    widget_token_max_age = positive_int(
        "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_MAX_AGE",
        setting(
            "DJANGOSPICE_LOOKUP_WIDGET_TOKEN_MAX_AGE",
            DEFAULT_WIDGET_TOKEN_MAX_AGE,
        ),
    )

    require_authentication = bool(
        setting(
            "DJANGOSPICE_LOOKUP_REQUIRE_AUTHENTICATION",
            DEFAULT_REQUIRE_AUTHENTICATION,
        ),
    )

    return LookupConfig(
        search_param=search_param,
        page_param=page_param,
        page_size_param=page_size_param,
        page=page,
        page_size=page_size,
        max_page_size=max_page_size,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithms=jwt_algorithms,
        jwt_user_claim=jwt_user_claim,
        jwt_user_resolver=jwt_user_resolver,
        widget_token_header=widget_token_header,
        widget_token_salt=widget_token_salt,
        widget_token_max_age=widget_token_max_age,
        require_authentication=require_authentication,
    )


lookup_config = get_lookup_config()