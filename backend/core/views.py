from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_safe


def _frontend_index_path() -> Path:
    return settings.BASE_DIR / "frontend_dist" / "index.html"


@require_safe
def frontend_app(request):
    if _frontend_index_path().exists():
        return render(request, "index.html")

    return JsonResponse(
        {
            "name": "Smart Agriculture Intelligence Platform",
            "version": "0.1.0",
            "backend": "Django",
            "frontend_built": False,
            "message": "Frontend build not found yet. Run the Vite production build to serve the dashboard from Django.",
            "modules": [
                "crop recommendation",
                "smart irrigation",
                "plant disease detection",
                "market forecasting",
                "multilingual chatbot",
                "unified dashboard integration",
            ],
        }
    )


@require_GET
def platform_info(request) -> JsonResponse:
    return JsonResponse(
        {
            "name": "Smart Agriculture Intelligence Platform",
            "version": "0.1.0",
            "backend": "Django",
            "frontend_built": _frontend_index_path().exists(),
        }
    )


@require_GET
def health_check(request) -> JsonResponse:
    return JsonResponse({"status": "ok"})
