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
        messages = payload.get("messages")
        if messages is not None and not isinstance(messages, list):
            raise ValueError("'messages' must be an array.")

        context = payload.get("context")
        if context is not None and not isinstance(context, dict):
            raise ValueError("'context' must be an object.")

        model_input = {
            "language": optional_string(payload, "language") or "en",
            "provider": optional_string(payload, "provider"),
            "messages": messages,
            "context": context or {},
            "crop": optional_string(payload, "crop"),
            "disease_name": optional_string(payload, "disease_name"),
        }
        if not messages:
            model_input["question"] = require_string(payload, "question")
    except (KeyError, ValueError) as exc:
        return json_error(get_error_message(exc))

    try:
        return JsonResponse(answer_farmer_question(model_input))
    except ValueError as exc:
        return json_error(get_error_message(exc))
