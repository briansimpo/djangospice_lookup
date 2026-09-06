# Djangospice Lookup

A reusable Django lookup widget and server-side lookup endpoint for selecting objects from large datasets.

`djangospice_lookup` provides an enhanced lookup experience for Django forms and `django-filter` while preserving Django's standard form and field behavior.

It supports server-side search, pagination, filtering, dependent lookups, multiple selection, authentication, access scoping, and HTMX-driven interfaces.

---

## Features

* Django form widget integration
* `django-filter` integration
* Server-side object search
* Server-side filtering
* Pagination
* Dependent/cascading lookups
* Single selection
* Multiple selection
* Initial Django form values
* Bound and submitted form values
* Access-controlled lookups
* Django session authentication
* JWT bearer authentication
* Short-lived widget capability tokens
* Configurable request parameters
* Configurable pagination
* Configurable authentication
* HTMX support
* Django template tags for assets
* Progressive enhancement
* JSON lookup endpoints

---

## Requirements

* Python 3.12+
* Django 5.0+
* `django-filter` when using `LookupWidget` with `django-filter`
* `PyJWT` for JWT authentication

---

# Installation

Install the package:

```bash
pip install djangospice-lookup
```

Add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "djangospice_lookup",
]
```

If the project uses `django-filter`:

```bash
pip install django-filter
```

and add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_filters",
    "djangospice_lookup",
]
```

---

# Configuration

`djangospice_lookup` uses Django settings for package-wide configuration.

All package settings use the `DJANGOSPICE_LOOKUP_` prefix.

## Search

Configure the search parameter:

```python
DJANGOSPICE_LOOKUP_SEARCH_PARAM = "q"
```

The default is:

```text
q
```

For example:

```text
/lookup/library/book/?q=django
```

---

## Pagination

Configure pagination parameters and limits:

```python
DJANGOSPICE_LOOKUP_PAGE_PARAM = "page"

DJANGOSPICE_LOOKUP_PAGE_SIZE_PARAM = "page_size"

DJANGOSPICE_LOOKUP_PAGE = 1

DJANGOSPICE_LOOKUP_PAGE_SIZE = 20

DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE = 100
```

These settings control:

* default page number
* page query parameter
* page-size query parameter
* default page size
* maximum page size

---

## Authentication Requirement

Authentication is required by default:

```python
DJANGOSPICE_LOOKUP_REQUIRE_AUTHENTICATION = True
```

For intentionally public lookup data:

```python
DJANGOSPICE_LOOKUP_REQUIRE_AUTHENTICATION = False
```

Only disable authentication when the lookup data is intentionally accessible without authentication.

---

## JWT Authentication

The default JWT secret can use Django's `SECRET_KEY`:

```python
DJANGOSPICE_LOOKUP_JWT_SECRET_KEY = SECRET_KEY
```

Configure the permitted algorithms:

```python
DJANGOSPICE_LOOKUP_JWT_ALGORITHMS = (
    "HS256",
)
```

The default user claim is:

```python
DJANGOSPICE_LOOKUP_JWT_USER_CLAIM = "user_id"
```

A custom user resolver can be configured using a dotted Python path:

```python
DJANGOSPICE_LOOKUP_JWT_USER_RESOLVER = (
    "myproject.authentication.resolve_user"
)
```

---

## Widget Capability Tokens

Configure the capability-token header:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_HEADER = (
    "X-Lookup-Token"
)
```

Configure the signing salt:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_SALT = (
    "djangospice_lookup.widget"
)
```

Configure the token lifetime in seconds:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_MAX_AGE = 300
```

The default lifetime is five minutes.

---

# URL Configuration

Include the package URLs in your project:

```python
from django.urls import include, path


urlpatterns = [
    path("", include("djangospice_lookup.urls")),
]
```

The package provides the canonical lookup endpoint:

```text
/lookup/<app_name>/<name>/
```

For example:

```text
/lookup/library/book/
```

The URL identifies a registered lookup using the Django application label and model name.

---

# Middleware

Add `LookupMiddleware` to your project's `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ...
    "djangospice_lookup.middleware.LookupMiddleware",
]
```

When using Django session authentication, place it after Django's `AuthenticationMiddleware`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "djangospice_lookup.middleware.LookupMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

`LookupMiddleware` works alongside Django authentication. It does not replace:

```python
"django.contrib.auth.middleware.AuthenticationMiddleware",
```

Django authentication remains responsible for establishing:

```python
request.user
```

The lookup system can then use the authenticated request when applying lookup security and access rules.

For JWT and widget capability authentication, lookup security can authenticate the request independently of the Django session.

---

# Registering Lookups

Lookups are explicitly registered.

This controls which models are exposed through lookup endpoints.

For example:

```python
from djangospice_lookup.registry import register_lookup

from .models import Author, Book


register_lookup(Author)
register_lookup(Book)
```

A typical application can keep registrations in `lookup.py`:

```text
library/
├── models.py
├── lookup.py
└── apps.py
```

Only explicitly registered models are exposed as lookups.

---

# Lookup Configuration

A lookup can optionally be configured when it is registered.

For example:

```python
register_lookup(
    Book,
    scope="account",
)
```

The `scope` identifies the relationship used to restrict results according to the authenticated user.

Django ORM relationship paths can be used:

```python
register_lookup(
    Book,
    scope="account__user",
)
```

This allows access restrictions to follow related objects.

---

# LookupWidget

The primary form integration is `LookupWidget`.

Import it with:

```python
from djangospice_lookup.widget import LookupWidget
```

It can be used with standard Django form fields.

## ModelChoiceField

```python
from django import forms

from djangospice_lookup.widget import LookupWidget

from .models import Book


class BookForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
        ),
    )
```

The widget provides a searchable remote lookup without requiring the entire queryset to be rendered into the initial HTML.

---

## ModelMultipleChoiceField

For multiple selections:

```python
class BookForm(forms.Form):
    books = forms.ModelMultipleChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
        ),
    )
```

The widget respects Django's native multiple-selection behavior.

---

# Using LookupWidget with django-filter

`LookupWidget` can be used directly as the widget for a `django-filter` field.

For example:

```python
import django_filters

from djangospice_lookup.widget import LookupWidget

from .models import Author, Book


class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
        ),
    )

    class Meta:
        model = Book
        fields = (
            "author",
        )
```

Render the filter normally:

```django
<form method="get">
    {{ filter.form.as_p }}

    <button type="submit">
        Filter
    </button>
</form>
```

The `author` filter now uses `LookupWidget` instead of a conventional select containing every author.

This is especially useful when the filter queryset contains a large number of records.

---

## Multiple Lookup Filters

Multiple filters can use `LookupWidget`:

```python
class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
        ),
    )

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        widget=LookupWidget(
            model=Category,
        ),
    )

    class Meta:
        model = Book
        fields = (
            "author",
            "category",
        )
```

---

## Multiple Selection with django-filter

Use `ModelMultipleChoiceFilter` for multiple selections:

```python
class BookFilter(django_filters.FilterSet):
    authors = django_filters.ModelMultipleChoiceFilter(
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
        ),
    )

    class Meta:
        model = Book
        fields = (
            "authors",
        )
```

---

# Dependent Lookups

A lookup can depend on another form field.

For example:

```python
class BookForm(forms.Form):
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
        ),
    )

    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
            depends_on=("author"),
        ),
    )
```

The book lookup can then use the selected author when requesting results.

Conceptually:

```text
Author
   ↓
Book
```

A request may look like:

```text
/lookup/library/book/?author=12
```

---

## Dependent django-filter Fields

Dependencies can also be used in a `FilterSet`:

```python
class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
        ),
    )

    book = django_filters.ModelChoiceFilter(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
            depends_on=("author"),
        ),
    )

    class Meta:
        model = Book
        fields = (
            "author",
            "book",
        )
```

This supports cascading relationships such as:

```text
Country → City
Department → Program
Program → Course
Category → Product
Author → Book
```

---

## Relationship Paths

Dependencies can reference related fields using normal Django ORM relationship paths:

```python
depends_on=(
    "account__user",
)
```

This allows dependencies to resolve through related objects.

---

# Search

Lookup fields support server-side text search.

For example:

```text
/lookup/library/book/?q=django
```

Search is performed by the lookup endpoint, allowing the browser to request only the records required for the current query.

The search parameter is configurable through:

```python
DJANGOSPICE_LOOKUP_SEARCH_PARAM = "q"
```

---

# Filtering

Lookup requests can contain filter values.

For example:

```text
/lookup/library/book/?author=12
```

Search and filtering can be combined:

```text
/lookup/library/book/?q=django&author=12
```

When `LookupWidget` is used with `django-filter`, the filter form remains responsible for filter semantics while the widget provides efficient remote selection of filter values.

---

# Pagination

Lookup results are paginated.

For example:

```text
/lookup/library/book/?page=2
```

A page size can also be supplied:

```text
/lookup/library/book/?page=2&page_size=50
```

Pagination prevents large querysets from being transferred to the browser in a single request.

The maximum page size is controlled by:

```python
DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE = 100
```

---

# Initial Values

`LookupWidget` works with Django's normal initial and bound field behavior.

For example:

```python
class BookForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
        ),
        initial=12,
    )
```

This makes the widget suitable for both create and edit forms.

---

# Django Form Validation

`LookupWidget` does not replace Django field validation.

For example:

```python
class BookForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
        ),
    )
```

Django continues to validate the submitted value against the field's queryset.

The widget helps the user select an object; the Django form field remains responsible for validating the submitted value.

---

# Access Control

Lookup results can be restricted according to the authenticated user.

For example:

```python
register_lookup(
    Book,
    scope="account",
)
```

A scoped lookup only returns objects satisfying the configured relationship.

This is useful when users should only be able to select objects belonging to their permitted account or organization.

The lookup endpoint should not be used to bypass the application's authorization rules.

---

# Authentication

The default security configuration supports:

1. Widget capability tokens
2. Django session authentication
3. JWT bearer authentication

## Django Session Authentication

Authenticated Django users can access lookup endpoints using their normal Django session.

No special authentication code is required in the widget.

---

## JWT Authentication

API clients can authenticate using:

```http
Authorization: Bearer <token>
```

JWT behavior is controlled through the package configuration.

---

## Widget Capability Tokens

A widget can use a short-lived capability token:

```http
X-Lookup-Token: <token>
```

Capability tokens provide short-lived access to a specific lookup.

---

# Template Tags

The package provides template tags for loading its frontend assets.

Load the template tag library:

```django
{% load djangospice_lookup %}
```

---

## Load All Assets

The simplest approach is:

```django
{% djangospice_lookup_assets %}
```

This loads both the lookup CSS and JavaScript.

A base template can use:

```django
{% load djangospice_lookup %}

<head>
    {% djangospice_lookup_assets %}
</head>
```

---

## Load CSS Only

```django
{% djangospice_lookup_css %}
```

---

## Load JavaScript Only

```django
{% djangospice_lookup_js %}
```

---

## Load Assets Separately

Applications that need more control can load the assets independently:

```django
{% load djangospice_lookup %}

<head>
    {% djangospice_lookup_css %}
</head>

<body>

    {% block content %}
    {% endblock %}

    {% djangospice_lookup_js %}
</body>
```

The template tags use Django's static-files system to resolve the package assets.

---

# HTMX

`LookupWidget` works with HTMX-driven interfaces.

Lookup fields can be rendered inside:

* dynamically loaded forms
* modal dialogs
* filter forms
* partial templates
* inline forms
* dynamically replaced form sections

When HTMX replaces part of a page, newly rendered lookup widgets can be initialized as part of the HTMX lifecycle.

---

# JSON Lookup Endpoint

The lookup endpoint returns JSON suitable for the widget and other clients.

A response has the general structure:

```json
{
    "results": [
        {
            "id": "8f3a...",
            "text": "Introduction to Django"
        },
        {
            "id": "91ab...",
            "text": "Advanced Django"
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "has_next": true
    }
}
```

The exact result values depend on the registered lookup and its configuration.

---

# Endpoint Examples

## Search

```http
GET /lookup/library/book/?q=django
```

## Filter

```http
GET /lookup/library/book/?author=12
```

## Search and Filter

```http
GET /lookup/library/book/?q=django&author=12
```

## Pagination

```http
GET /lookup/library/book/?page=2&page_size=20
```

## Dependent Lookup

```http
GET /lookup/library/book/?author=12
```

---

# Complete Example

The following example demonstrates a typical Django application using `LookupWidget` with `django-filter`.

## Models

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(
        max_length=200,
    )

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(
        max_length=200,
    )

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title
```

---

## Lookup Registration

```python
from djangospice_lookup.registry import register_lookup

from .models import Author, Book


register_lookup(Author)
register_lookup(Book)
```

---

## Filter

```python
import django_filters

from djangospice_lookup.widget import LookupWidget

from .models import Author, Book


class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        label="Author",
        queryset=Author.objects.all(),
        widget=LookupWidget(
            model=Author,
            placeholder="Select an author",
            search_placeholder="Search authors...",
        ),
    )

    class Meta:
        model = Book
        fields = (
            "author",
        )
```

---

## View

```python
from django.views.generic import ListView

from .filters import BookFilter
from .models import Book


class BookListView(ListView):
    model = Book
    template_name = "library/book_list.html"

    def get_queryset(self):
        self.filter = BookFilter(
            self.request.GET,
            queryset=Book.objects.all(),
        )

        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        return context
```

---

## Template

```django
{% load djangospice_lookup %}

{% djangospice_lookup_assets %}

<form method="get">
    {{ filter.form.as_p }}

    <button type="submit">
        Filter
    </button>
</form>

{% for book in object_list %}
    <article>
        <h2>{{ book.title }}</h2>
        <p>{{ book.author }}</p>
    </article>
{% endfor %}
```

---

# Progressive Enhancement

`LookupWidget` is built around Django's standard `<select>` widget.

The underlying form control remains part of the HTML form.

This preserves Django's existing:

* form fields
* validation
* initial values
* bound values
* submitted values
* required state
* disabled state
* multiple-selection behavior

The lookup interface enhances the field when the package assets are loaded.

---

# Recommended Usage

`djangospice_lookup` is particularly useful when a form or filter needs to select from a large queryset.

For small static choice sets, a normal Django `ChoiceField` or `ModelChoiceField` may be sufficient.

For large or frequently changing datasets, `LookupWidget` provides a more scalable selection experience.

---

# License

This package is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.
