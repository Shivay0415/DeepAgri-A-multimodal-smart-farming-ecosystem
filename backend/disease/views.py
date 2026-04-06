from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import json_error
from disease.services import analyze_leaf_image


@csrf_exempt
@require_POST
def disease_detect(request) -> JsonResponse:
    image = request.FILES.get("image")
    crop = str(request.POST.get("crop", "")).strip()
    symptom_hint = request.POST.get("symptom_hint")

    if image is None:
        return json_error("'image' file is required.")
    if not crop:
        return json_error("'crop' is required.")

    response = analyze_leaf_image(
        filename=image.name,
        image_size_bytes=image.size,
        crop=crop,
        symptom_hint=symptom_hint,
    )
    return JsonResponse(response)

