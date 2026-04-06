from django.urls import path

from core import views


urlpatterns = [
    path("", views.root, name="root"),
    path("health/", views.health_check, name="health"),
]
