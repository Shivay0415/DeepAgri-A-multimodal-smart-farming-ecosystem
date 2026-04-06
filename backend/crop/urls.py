from django.urls import path

from crop import views


urlpatterns = [
    path("recommend/", views.crop_recommendation, name="crop-recommendation"),
]

