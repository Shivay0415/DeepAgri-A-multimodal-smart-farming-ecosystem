from django.urls import path

from chatbot import views


urlpatterns = [
    path("ask/", views.ask_agri_bot, name="ask-agri-bot"),
]
