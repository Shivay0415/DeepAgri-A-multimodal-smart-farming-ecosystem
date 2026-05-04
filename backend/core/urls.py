from django.urls import path, re_path

from core import views


urlpatterns = [
    path("", views.frontend_app, name="root"),
    path("health/", views.health_check, name="health"),
    path("api/meta/", views.platform_info, name="platform_info"),
    re_path(r"^(?!api/|admin/|health/|static/).*$", views.frontend_app, name="frontend"),
]
