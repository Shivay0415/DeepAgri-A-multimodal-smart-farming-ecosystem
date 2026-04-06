import json

from django.http import JsonResponse


def json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def get_error_message(exc: Exception) -> str:
    return str(exc.args[0]) if getattr(exc, "args", None) else str(exc)


def parse_json_body(request) -> dict:
    if not request.body:
        return {}

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Request body must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object.")
    return payload


def require_float(
    payload: dict,
    field: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if field not in payload:
        raise KeyError(f"'{field}' is required.")

    try:
        value = float(payload[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' must be a number.") from exc

    if min_value is not None and value < min_value:
        raise ValueError(f"'{field}' must be at least {min_value}.")
    if max_value is not None and value > max_value:
        raise ValueError(f"'{field}' must be at most {max_value}.")
    return value


def optional_float(
    payload: dict,
    field: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    if field not in payload or payload[field] in (None, ""):
        return None

    try:
        value = float(payload[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' must be a number.") from exc

    if min_value is not None and value < min_value:
        raise ValueError(f"'{field}' must be at least {min_value}.")
    if max_value is not None and value > max_value:
        raise ValueError(f"'{field}' must be at most {max_value}.")
    return value


def require_int(
    payload: dict,
    field: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if field not in payload:
        raise KeyError(f"'{field}' is required.")

    try:
        value = int(payload[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' must be an integer.") from exc

    if min_value is not None and value < min_value:
        raise ValueError(f"'{field}' must be at least {min_value}.")
    if max_value is not None and value > max_value:
        raise ValueError(f"'{field}' must be at most {max_value}.")
    return value


def optional_string(payload: dict, field: str) -> str | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    return str(value).strip()


def optional_boolean(payload: dict, field: str, default: bool = False) -> bool:
    if field not in payload:
        return default

    value = payload[field]
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off", ""}:
        return False
    raise ValueError(f"'{field}' must be a boolean.")


def require_string(payload: dict, field: str) -> str:
    value = optional_string(payload, field)
    if not value:
        raise KeyError(f"'{field}' is required.")
    return value
