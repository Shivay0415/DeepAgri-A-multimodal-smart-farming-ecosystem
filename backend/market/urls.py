from django.urls import path

from market import views


urlpatterns = [
    path("forecast/", views.market_forecast, name="market-forecast"),
]

