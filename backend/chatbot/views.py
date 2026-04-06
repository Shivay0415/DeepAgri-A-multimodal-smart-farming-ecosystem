from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from chatbot.services import answer_farmer_question
from core.utils import (
    get_error_message,
    json_error,
    optional_string,
    parse_json_body,
    require_string,
)


@csrf_exempt
@require_POST
def ask_agri_bot(request) -> JsonResponse:
    try:
        payload = parse_json_body(request)
        model_input = {
            "question": require_string(payload, "question"),
            "language": optional_string(payload, "language") or "en",
            "crop": optional_string(payload, "crop"),
            "disease_name": optional_string(payload, "disease_name"),
        }
    except (KeyError, ValueError) as exc:
        return json_error(get_error_message(exc))

    return JsonResponse(answer_farmer_question(model_input))
