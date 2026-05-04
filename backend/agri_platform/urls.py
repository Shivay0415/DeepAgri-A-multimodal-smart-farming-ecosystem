from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/crop/", include("crop.urls")),
    path("api/v1/irrigation/", include("irrigation.urls")),
    path("api/v1/disease/", include("disease.urls")),
    path("api/v1/market/", include("market.urls")),
    path("api/v1/chat/", include("chatbot.urls")),
    path("", include("core.urls")),
]
