from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderRequestError(RuntimeError):
    """Raised when an upstream AI provider request fails."""


def _extract_error_message(payload: dict) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if message:
            return str(message)
    if isinstance(error, str) and error.strip():
        return error.strip()
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def post_json(url: str, payload: dict, headers: dict[str, str], timeout: float) -> dict:
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            parsed = {}
        message = _extract_error_message(parsed) or f"Provider request failed with HTTP {exc.code}."
        raise ProviderRequestError(message) from exc
    except URLError as exc:
        raise ProviderRequestError(
            "Could not connect to the AI provider. Check the internet connection and API key."
        ) from exc

    try:
        data = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise ProviderRequestError("Provider returned an invalid JSON response.") from exc

    if not isinstance(data, dict):
        raise ProviderRequestError("Provider returned an unexpected response format.")
    return data
