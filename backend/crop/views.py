from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import (
    get_error_message,
    json_error,
    optional_float,
    optional_string,
    parse_json_body,
    require_float,
)
from crop.services import recommend_crop


@csrf_exempt
@require_POST
def crop_recommendation(request) -> JsonResponse:
    try:
        payload = parse_json_body(request)
        model_input = {
            "nitrogen": require_float(payload, "nitrogen", min_value=0),
            "phosphorus": require_float(payload, "phosphorus", min_value=0),
            "potassium": require_float(payload, "potassium", min_value=0),
            "ph": require_float(payload, "ph", min_value=0, max_value=14),
            "temperature_c": optional_float(payload, "temperature_c"),
            "humidity_pct": optional_float(payload, "humidity_pct", min_value=0, max_value=100),
            "rainfall_mm": optional_float(payload, "rainfall_mm", min_value=0),
            "location": optional_string(payload, "location"),
        }
    except (KeyError, ValueError) as exc:
        return json_error(get_error_message(exc))

    return JsonResponse(recommend_crop(model_input))
