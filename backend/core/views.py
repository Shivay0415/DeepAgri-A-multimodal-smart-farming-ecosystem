from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def root(request) -> JsonResponse:
    return JsonResponse(
        {
            "name": "Smart Agriculture Intelligence Platform",
            "version": "0.1.0",
            "backend": "Django",
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
def health_check(request) -> JsonResponse:
    return JsonResponse({"status": "ok"})

