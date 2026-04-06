from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import (
    get_error_message,
    json_error,
    optional_float,
    optional_string,
    parse_json_body,
    require_int,
    require_string,
)
from market.services import forecast_market


@csrf_exempt
@require_POST
def market_forecast(request) -> JsonResponse:
    try:
        payload = parse_json_body(request)
        model_input = {
            "crop": require_string(payload, "crop"),
            "current_price_per_quintal": optional_float(
                payload, "current_price_per_quintal", min_value=0.1
            ),
            "expected_yield_tons": optional_float(payload, "expected_yield_tons", min_value=0.1),
            "horizon_days": require_int(
                {"horizon_days": payload.get("horizon_days", 14)},
                "horizon_days",
                min_value=3,
                max_value=30,
            ),
            "market_name": optional_string(payload, "market_name"),
        }
        if model_input["expected_yield_tons"] is None:
            raise KeyError("'expected_yield_tons' is required.")
    except (KeyError, ValueError) as exc:
        return json_error(get_error_message(exc))

    try:
        response = forecast_market(model_input)
    except ValueError as exc:
        return json_error(get_error_message(exc))

    return JsonResponse(response)
