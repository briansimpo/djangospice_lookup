from django.urls import path

from .views import LookupView
from .apps import namespace


urlpatterns = [
    path(
        "lookup/<str:app_label>/<str:name>/",
        LookupView.as_view(),
        name=namespace,
    ),
    
]