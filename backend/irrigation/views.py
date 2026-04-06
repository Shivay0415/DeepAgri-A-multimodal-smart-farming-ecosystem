from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import (
    get_error_message,
    json_error,
    optional_boolean,
    optional_float,
    optional_string,
    parse_json_body,
    require_float,
    require_string,
)
from irrigation.services import create_irrigation_plan


@csrf_exempt
@require_POST
def irrigation_plan(request) -> JsonResponse:
    try:
        payload = parse_json_body(request)
        use_live_weather = optional_boolean(payload, "use_live_weather", default=False)
        model_input = {
            "crop": require_string(payload, "crop"),
            "soil_moisture_pct": require_float(payload, "soil_moisture_pct", min_value=0, max_value=100),
            "rainfall_forecast_mm": optional_float(payload, "rainfall_forecast_mm", min_value=0),
            "temperature_c": optional_float(payload, "temperature_c", min_value=-20, max_value=60),
            "humidity_pct": optional_float(payload, "humidity_pct", min_value=0, max_value=100),
            "area_hectares": require_float(payload, "area_hectares", min_value=0.1),
            "growth_stage": require_string(payload, "growth_stage"),
            "location": optional_string(payload, "location"),
            "use_live_weather": use_live_weather,
        }

        if not use_live_weather:
            for field in ("rainfall_forecast_mm", "temperature_c", "humidity_pct"):
                if model_input[field] is None:
                    raise KeyError(
                        f"'{field}' is required unless live weather is enabled with a valid location."
                    )
    except (KeyError, ValueError) as exc:
        return json_error(get_error_message(exc))

    try:
        response = create_irrigation_plan(model_input)
    except ValueError as exc:
        return json_error(get_error_message(exc))

    return JsonResponse(response)
