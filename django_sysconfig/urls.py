from django.urls import path

from .views import ConfigAppDetailView, ConfigAppListView

app_name = "django_sysconfig"

urlpatterns = [
    path("", ConfigAppListView.as_view(), name="app_list"),
    path("<str:app_label>/", ConfigAppDetailView.as_view(), name="app_detail"),
]
