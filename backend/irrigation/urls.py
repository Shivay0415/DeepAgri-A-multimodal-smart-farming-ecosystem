from django.urls import path

from irrigation import views


urlpatterns = [
    path("plan/", views.irrigation_plan, name="irrigation-plan"),
]

