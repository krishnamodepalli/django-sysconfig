"""
URL configuration for the local development server.
Wires up Django admin + the django_sysconfig config UI.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin/config/", include("django_sysconfig.urls")),
]
