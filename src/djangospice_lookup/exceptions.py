from __future__ import annotations


class LookupError(Exception):
    """Base exception for lookup errors."""


class LookupConfigurationError(LookupError):
    """Invalid lookup configuration."""


class LookupModelNotFound(LookupError):
    """A lookup model could not be resolved."""


class LookupNotAllowed(LookupError):
    """A lookup is not allowed."""


class InvalidLookupQuery(LookupError):
    """A lookup query is invalid."""


class InvalidLookupDependency(LookupError):
    """A lookup dependency is invalid."""


class InvalidLookupField(LookupError):
    """A lookup field or relationship path is invalid."""


class AmbiguousLookupDependency(LookupError):
    """A model dependency maps to multiple relationships."""


class InvalidLookupSearch(LookupError):
    """A lookup search configuration is invalid."""


class InvalidLookupOrdering(LookupError):
    """A lookup ordering configuration is invalid."""


class AuthenticationError(Exception):
    """Raised when authentication credentials are invalid."""


class AuthenticationRequired(AuthenticationError):
    """Raised when authentication is required but unavailable."""
