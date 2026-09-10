from __future__ import annotations

from django import template
from django.templatetags.static import static
from djangospice_lookup.apps import namespace

register = template.Library()


LOOKUP_CSS = f"{namespace}/css/lookup.css"
LOOKUP_JS = f"{namespace}/js/lookup.js"


def _lookup_css() -> str:
    return (
        f'<link rel="stylesheet" href="{static(LOOKUP_CSS)}">'
    )


def _lookup_js() -> str:
    return (
        f'<script src="{static(LOOKUP_JS)}" defer></script>'
    )


@register.simple_tag
def djangospice_lookup_css() -> str:
    """Render the DjangoSpice Lookup stylesheet."""
    return _lookup_css()


@register.simple_tag
def djangospice_lookup_js() -> str:
    """Render the DjangoSpice Lookup JavaScript."""
    return _lookup_js()


@register.simple_tag
def djangospice_lookup_assets() -> str:
    """Render all DjangoSpice Lookup assets."""
    return "\n".join(
        (
            _lookup_css(),
            _lookup_js(),
        )
    )