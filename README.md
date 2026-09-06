# DjangoSpice Lookup

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

* Python
* Django
* `django-filter` when using lookup widgets with Django FilterSets

Install `django-filter` separately if your project uses it:

```bash
pip install django-filter
```

---

# Installation

Install the package:

```bash
pip install djangospice-lookup
```

Add it to your Django project:

```python
INSTALLED_APPS = [
    # ...
    "djangospice_lookup",
]
```

If you use `django-filter`:

```python
INSTALLED_APPS = [
    # ...
    "django_filters",
    "djangospice_lookup",
]
```

---

# URL Configuration

Include the package URLs in your project:

```python
from django.urls import include, path


urlpatterns = [
    path("", include("djangospice_lookup.urls")),
]
```

This provides the canonical lookup endpoint:

```text
/lookup/<app_name>/<name>/
```

For example:

```text
/lookup/library/book/
```

The URL identifies a registered lookup using the model's Django application label and model name.

---

# Registering Lookups

Lookups are explicitly registered.

This allows an application to decide which models are available through the lookup endpoint.

For example:

```python
from djangospice_lookup.registry import register_lookup

from .models import Book


register_lookup(Book)
```

A lookup registration can be kept in the application's `lookup.py`:

```text
library/
├── models.py
├── lookup.py
└── apps.py
```

A typical `lookup.py` might contain:

```python
from djangospice_lookup.registry import register_lookup

from .models import Author, Book


register_lookup(Author)
register_lookup(Book)
```

Only models explicitly registered as lookups are exposed.

---

# Lookup Configuration

A lookup can be configured when it is registered.

For example:

```python
register_lookup(
    Book,
    scope="account",
)
```

The `scope` defines the relationship used to restrict lookup results to objects accessible to the authenticated user.

Relationship paths can use normal Django ORM lookup syntax:

```python
register_lookup(
    Book,
    scope="account",
)
```

or:

```python
register_lookup(
    Book,
    scope="account__user",
)
```

The exact options available depend on the package version.

---

# LookupWidget

The main form integration is `LookupWidget`.

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

The widget provides a searchable remote lookup instead of requiring every object to be rendered into the initial HTML.

---

# ModelMultipleChoiceField

For multiple selections, use `ModelMultipleChoiceField`:

```python
class BookForm(forms.Form):
    books = forms.ModelMultipleChoiceField(
        queryset=Book.objects.all(),
        widget=LookupWidget(
            model=Book,
        ),
    )
```

The widget respects the field's native multiple-selection behavior.

Selected objects are retained as normal Django form values.

---

# Using `LookupWidget` with django-filter

`LookupWidget` integrates directly with `django-filter`.

The widget is supplied to the filter field in the same way that any Django form widget would be supplied.

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

The filter form can then be rendered normally:

```django
<form method="get">
    {{ filter.form.as_p }}

    <button type="submit">
        Filter
    </button>
</form>
```

The `author` filter is therefore backed by `LookupWidget` rather than a conventional select containing every author.

This is especially useful when the filter queryset contains thousands or millions of records.

---

# Multiple django-filter Lookup Fields

Multiple filter fields can use `LookupWidget`.

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

Each lookup field operates independently while following the same lookup configuration and endpoint conventions.

---

# Multiple Selection with django-filter

`LookupWidget` can also be used with `ModelMultipleChoiceFilter`.

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

This allows users to select multiple related objects without rendering the entire queryset as a large HTML select.

---

# Dependent Lookups

Lookup fields can depend on other form fields.

For example, suppose a book belongs to an author.

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
            depends_on={
                "author": "author",
            },
        ),
    )
```

The book lookup can use the selected author when requesting its results.

Conceptually:

```text
Author
   ↓
Book
```

When the user selects an author, the book lookup can request:

```text
/lookup/library/book/?author=12
```

---

# Dependent django-filter Fields

The same approach can be used in a `FilterSet`.

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
            depends_on={
                "author": "author",
            },
        ),
    )

    class Meta:
        model = Book
        fields = (
            "author",
            "book",
        )
```

This is useful for common cascading filter relationships such as:

```text
Country → City
Department → Program
Program → Course
Category → Product
Author → Book
```

---

# Relationship Paths

Dependencies can reference related fields using Django ORM relationship paths.

For example:

```python
depends_on={
    "account": "account__user",
}
```

This allows the dependency to resolve through related objects rather than requiring a direct field relationship.

---

# Search

Lookup fields support server-side text search.

For example:

```text
/lookup/library/book/?q=django
```

The default search parameter is:

```text
q
```

The parameter name can be configured.

Search is performed against the lookup endpoint, allowing the browser to request only the records needed for the current query.

---

# Filtering

Lookup requests can include filter parameters.

For example:

```text
/lookup/library/book/?author=12
```

Search and filtering can be combined:

```text
/lookup/library/book/?q=django&author=12
```

When `LookupWidget` is used with `django-filter`, the filter form remains responsible for the filter semantics while the widget provides efficient remote selection of filter values.

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

The maximum permitted page size can be configured.

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

Existing selections can therefore be rendered normally when editing an object.

---

# Django Form Validation

The widget does not replace Django's field validation.

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

The lookup widget is responsible for helping users select values; the Django form field remains responsible for validation.

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

This is useful in multi-user applications where users should only be able to select objects belonging to their permitted account or organization.

The lookup therefore should not be treated as a mechanism for bypassing the application's normal authorization rules.

---

# Authentication

Lookup requests can use the configured authentication mechanisms.

The default security configuration supports:

1. Widget capability tokens
2. Django session authentication
3. JWT bearer authentication

## Django Session Authentication

Authenticated Django users can access lookup endpoints using the normal Django session.

No special authentication code is required in the widget.

---

## JWT Authentication

API clients can authenticate using a bearer token:

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

Capability tokens are intended for short-lived lookup access and are associated with the lookup they authorize.

---

# Configuration

Package configuration is controlled through Django settings.

All package settings use the:

```text
DJANGOSPICE_LOOKUP_
```

prefix.

## Search Parameters

```python
DJANGOSPICE_LOOKUP_SEARCH_PARAM = "q"
```

Controls the query-string parameter used for text search.

Default:

```text
q
```

---

## Pagination Parameters

```python
DJANGOSPICE_LOOKUP_PAGE_PARAM = "page"

DJANGOSPICE_LOOKUP_PAGE_SIZE_PARAM = "page_size"

DJANGOSPICE_LOOKUP_PAGE = 1

DJANGOSPICE_LOOKUP_PAGE_SIZE = 20

DJANGOSPICE_LOOKUP_MAX_PAGE_SIZE = 100
```

These control:

* default page number
* page parameter
* page-size parameter
* default page size
* maximum page size

---

## JWT Configuration

The default JWT secret can use Django's `SECRET_KEY`:

```python
DJANGOSPICE_LOOKUP_JWT_SECRET_KEY = SECRET_KEY
```

Algorithms can be configured:

```python
DJANGOSPICE_LOOKUP_JWT_ALGORITHMS = (
    "HS256",
)
```

The default user claim is:

```python
DJANGOSPICE_LOOKUP_JWT_USER_CLAIM = "user_id"
```

A custom user resolver can be supplied:

```python
DJANGOSPICE_LOOKUP_JWT_USER_RESOLVER = (
    "myproject.authentication.resolve_user"
)
```

The resolver is responsible for resolving the authenticated user represented by the configured JWT claim.

---

## Widget Token Configuration

The widget capability-token header can be configured:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_HEADER = (
    "X-Lookup-Token"
)
```

The signing salt can be configured:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_SALT = (
    "djangospice_lookup.widget"
)
```

The token lifetime is configurable in seconds:

```python
DJANGOSPICE_LOOKUP_WIDGET_TOKEN_MAX_AGE = 300
```

The default lifetime is five minutes.

---

## Authentication Requirement

Authentication is required by default:

```python
DJANGOSPICE_LOOKUP_REQUIRE_AUTHENTICATION = True
```

For applications that intentionally expose public lookup data:

```python
DJANGOSPICE_LOOKUP_REQUIRE_AUTHENTICATION = False
```

Only disable authentication when the lookup data is deliberately intended to be publicly accessible.

---

# Template Tags

The package provides template tags for loading its frontend assets.

First load the template tag library:

```django
{% load djangospice_lookup %}
```

---

## Load All Assets

The simplest option is:

```django
{% djangospice_lookup_assets %}
```

This loads both the lookup stylesheet and JavaScript.

A common base-template usage is:

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

This renders the lookup stylesheet.

---

## Load JavaScript Only

```django
{% djangospice_lookup_js %}
```

This renders the lookup JavaScript.

---

## Separate CSS and JavaScript

Applications that prefer to control where assets are included can load them separately:

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

`LookupWidget` is designed to work with HTMX-driven interfaces.

Lookup fields can be rendered inside:

* dynamically loaded forms
* modal dialogs
* filter forms
* partial templates
* inline forms
* dynamically replaced form sections

When HTMX replaces part of a page, newly rendered lookup widgets can be initialized as part of the HTMX lifecycle.

---

# Using LookupWidget in a Filter Form

A complete example using Django FilterSets might look like this:

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

The template:

```django
{% load djangospice_lookup %}

{% djangospice_lookup_assets %}

<form method="get">
    {{ filter.form.as_p }}

    <button type="submit">
        Apply filters
    </button>
</form>
```

This gives the user a searchable author filter without rendering the complete author queryset into the initial page.

---

# Complete Example

The following demonstrates a typical setup.

## Model

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

## Lookup Registration

```python
from djangospice_lookup.registry import register_lookup

from .models import Author, Book


register_lookup(Author)
register_lookup(Book)
```

## Filter

```python
import django_filters

from djangospice_lookup.widget import LookupWidget

from .models import Author, Book


class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
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

# Progressive Enhancement

`LookupWidget` is built around Django's standard select widget.

The underlying form control remains part of the HTML form.

This means the widget works with Django's existing:

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

Typical use cases include:

* users
* students
* employees
* customers
* suppliers
* accounts
* departments
* programs
* courses
* products
* projects
* locations
* categories
* organizations

For small static choice sets, a normal Django `ChoiceField` or `ModelChoiceField` may be sufficient.

For large or frequently changing datasets, `LookupWidget` provides a more scalable selection experience.

---

# Design Principles

`djangospice_lookup` is intended to fit naturally into the Django ecosystem.

The package follows several principles:

### Django Forms First

The lookup is a Django form widget rather than a replacement form system.

### Server-Side Data

Large querysets are searched and paginated on the server instead of being loaded entirely into the browser.

### Standard Field Validation

Django form fields remain responsible for validating submitted values.

### Explicit Exposure

Applications explicitly register the models they want to expose as lookups.

### Configurable

Search, pagination, authentication, and widget behavior can be configured through Django settings.

### Reusable

The same lookup widget can be used in ordinary Django forms and `django-filter` forms.

---

# Summary

A typical integration consists of four steps:

### 1. Install

```bash
pip install djangospice-lookup
```

### 2. Register

```python
from djangospice_lookup.registry import register_lookup

register_lookup(Book)
```

### 3. Use the widget

```python
from djangospice_lookup.widget import LookupWidget

widget = LookupWidget(
    model=Book,
)
```

Or use it directly in a Django field:

```python
book = forms.ModelChoiceField(
    queryset=Book.objects.all(),
    widget=LookupWidget(
        model=Book,
    ),
)
```

### 4. Load the assets

```django
{% load djangospice_lookup %}

{% djangospice_lookup_assets %}
```

For `django-filter`, use the same widget directly on the filter field:

```python
author = django_filters.ModelChoiceFilter(
    queryset=Author.objects.all(),
    widget=LookupWidget(
        model=Author,
    ),
)
```

This provides a consistent, server-side lookup experience across Django forms and filter forms.

---

# License

This project is licensed under the terms specified by the project.
