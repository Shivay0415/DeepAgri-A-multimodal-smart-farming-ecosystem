from django.urls import path

from disease import views


urlpatterns = [
    path("detect/", views.disease_detect, name="disease-detect"),
]

