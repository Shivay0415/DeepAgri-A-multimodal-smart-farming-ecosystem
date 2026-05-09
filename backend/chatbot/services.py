from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from chatbot.providers import ProviderRequestError, post_json


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "data" / "agri_knowledge_base.json"
LANGUAGE_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
}


@lru_cache(maxsize=1)
def _load_knowledge_base() -> list[dict]:
    with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as knowledge_file:
        return json.load(knowledge_file)


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _normalize_language(language: str | None) -> str:
    normalized = _clean_text(language).lower()
    return normalized if normalized in LANGUAGE_LABELS else "en"


def _context_from_payload(payload: dict) -> dict:
    context = payload.get("context")
    if isinstance(context, dict):
        normalized = {
            key: _clean_text(value)
            for key, value in context.items()
            if _clean_text(value)
        }
    else:
        normalized = {}

    crop = _clean_text(payload.get("crop"))
    disease_name = _clean_text(payload.get("disease_name"))
    if crop and "crop" not in normalized:
        normalized["crop"] = crop
    if disease_name and "disease_name" not in normalized:
        normalized["disease_name"] = disease_name
    return normalized


def _normalize_messages(payload: dict) -> list[dict]:
    normalized_messages: list[dict] = []
    raw_messages = payload.get("messages")

    if isinstance(raw_messages, list):
        for message in raw_messages[-12:]:
            if not isinstance(message, dict):
                continue

            role = _clean_text(message.get("role")).lower()
            if role not in {"user", "assistant"}:
                continue

            content = _clean_text(message.get("content"))
            if not content:
                continue

            normalized_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    if not normalized_messages:
        question = _clean_text(payload.get("question"))
        if question:
            normalized_messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

    if not normalized_messages:
        raise ValueError("A question or a messages array is required.")
    return normalized_messages


def _build_signal(payload: dict, messages: list[dict]) -> str:
    context = _context_from_payload(payload)
    parts = [message["content"] for message in messages if message["role"] == "user"]
    parts.extend(context.values())
    return " ".join(parts).lower()


def _score_entry(entry: dict, signal: str) -> int:
    score = 0
    for keyword in entry["keywords"]:
        keyword_text = keyword.lower()
        if keyword_text in signal:
            score += 3 if " " in keyword_text else 2
    if entry["id"].replace("-", " ") in signal:
        score += 1
    return score


def _select_entries(payload: dict, messages: list[dict]) -> list[dict]:
    signal = _build_signal(payload, messages)
    ranked_entries: list[tuple[int, dict]] = []
    for entry in _load_knowledge_base():
        score = _score_entry(entry, signal)
        if score > 0:
            ranked_entries.append((score, entry))

    ranked_entries.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in ranked_entries[:3]]


def _localized_answer(entry: dict, language: str) -> str:
    key = {
        "en": "answer_en",
        "hi": "answer_hi",
        "ta": "answer_ta",
    }.get(language, "answer_en")
    return entry.get(key) or entry["answer_en"]


def _build_grounding_notes(entries: list[dict], language: str) -> str:
    if not entries:
        return "No direct knowledge-base match was found, so answer using general agricultural reasoning."

    notes = [
        f"- {entry['id']}: {_localized_answer(entry, language)}"
        for entry in entries
    ]
    return "\n".join(notes)


def _build_module_context(payload: dict) -> str:
    context = _context_from_payload(payload)
    lines = []

    if context.get("crop"):
        lines.append(f"Recommended crop: {context['crop']}")
    if context.get("crop_summary"):
        lines.append(f"Crop module summary: {context['crop_summary']}")
    if context.get("disease_name"):
        lines.append(f"Detected disease: {context['disease_name']}")
    if context.get("disease_summary"):
        lines.append(f"Disease module summary: {context['disease_summary']}")
    if context.get("irrigation_summary"):
        lines.append(f"Irrigation module summary: {context['irrigation_summary']}")
    if context.get("market_summary"):
        lines.append(f"Market module summary: {context['market_summary']}")

    return "\n".join(lines) if lines else "No module context is currently available."


def _serialize_conversation(messages: list[dict]) -> str:
    lines = []
    for message in messages:
        speaker = "Farmer" if message["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {message['content']}")
    return "\n".join(lines)


def _configured_providers() -> list[str]:
    providers = []
    if settings.OPENAI_API_KEY:
        providers.append("openai")
    if settings.GEMINI_API_KEY:
        providers.append("gemini")
    return providers


def _resolve_provider(requested_provider: str | None) -> dict:
    requested = _clean_text(requested_provider or settings.AGRI_BOT_PROVIDER).lower() or "auto"
    if requested == "chatgpt":
        requested = "openai"
    if requested not in {"auto", "openai", "gemini", "local"}:
        requested = "auto"

    if requested == "openai":
        if settings.OPENAI_API_KEY:
            return {
                "requested": requested,
                "active": "openai",
                "model": settings.OPENAI_CHAT_MODEL,
                "notice": None,
            }
        return {
            "requested": requested,
            "active": "local",
            "model": None,
            "notice": "OPENAI_API_KEY is not configured, so the Agri-Bot is using the local fallback.",
        }

    if requested == "gemini":
        if settings.GEMINI_API_KEY:
            return {
                "requested": requested,
                "active": "gemini",
                "model": settings.GEMINI_MODEL,
                "notice": None,
            }
        return {
            "requested": requested,
            "active": "local",
            "model": None,
            "notice": "GEMINI_API_KEY is not configured, so the Agri-Bot is using the local fallback.",
        }

    if requested == "local":
        return {
            "requested": requested,
            "active": "local",
            "model": None,
            "notice": "The Agri-Bot is pinned to the local agriculture fallback.",
        }

    if settings.OPENAI_API_KEY:
        return {
            "requested": requested,
            "active": "openai",
            "model": settings.OPENAI_CHAT_MODEL,
            "notice": None,
        }
    if settings.GEMINI_API_KEY:
        return {
            "requested": requested,
            "active": "gemini",
            "model": settings.GEMINI_MODEL,
            "notice": None,
        }
    return {
        "requested": requested,
        "active": "local",
        "model": None,
        "notice": "No external AI provider is configured. Add OPENAI_API_KEY or GEMINI_API_KEY in backend/.env to enable full open-ended answers.",
    }


def _build_system_prompt(payload: dict, language: str, entries: list[dict]) -> str:
    language_name = LANGUAGE_LABELS[language]
    return (
        "You are AgriPulse AI, a practical agriculture assistant for farmers.\n"
        f"Always answer in {language_name}.\n"
        "Keep the response clear, warm, and useful.\n"
        "Prefer short paragraphs or flat bullet points.\n"
        "Use the supplied module context when it is relevant.\n"
        "Ground your answer in the retrieved agriculture notes when they apply, but you may also use general agricultural reasoning.\n"
        "If a question asks for exact pesticide dosage, legal compliance, or anything unsafe, do not invent precise chemical instructions. Give a safe high-level answer and tell the user to follow local label guidance or consult a local agronomist.\n"
        "If the question is outside agriculture, still answer helpfully and concisely.\n\n"
        "Current farm context:\n"
        f"{_build_module_context(payload)}\n\n"
        "Retrieved agriculture notes:\n"
        f"{_build_grounding_notes(entries, language)}"
    )


def _extract_openai_text(payload: dict) -> str:
    fragments: list[str] = []
    for choice in payload.get("choices", []):
        if not isinstance(choice, dict):
            continue
        message = choice.get("message") or {}
        text = _clean_text(message.get("content"))
        if text:
            fragments.append(text)

    if fragments:
        return "\n\n".join(fragments)
    raise ProviderRequestError("OpenAI returned no text answer.")


def _extract_gemini_text(payload: dict) -> str:
    fragments: list[str] = []
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if not isinstance(part, dict):
                continue
            text = _clean_text(part.get("text"))
            if text:
                fragments.append(text)

    if fragments:
        return "\n\n".join(fragments)
    raise ProviderRequestError("Gemini returned no text answer.")


def _call_openai(messages: list[dict], payload: dict, language: str, entries: list[dict]) -> dict:
    system_prompt = _build_system_prompt(payload, language, entries)
    api_messages = [
        {"role": "system", "content": system_prompt},
    ] + messages
    
    response = post_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": settings.OPENAI_CHAT_MODEL,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        },
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=settings.AGRI_BOT_TIMEOUT_SECONDS,
    )
    return {
        "answer": _extract_openai_text(response),
        "provider_name": "openai",
        "provider_label": "OpenAI ChatGPT",
        "model": settings.OPENAI_CHAT_MODEL,
    }


def _call_gemini(messages: list[dict], payload: dict, language: str, entries: list[dict]) -> dict:
    response = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
        {
            "system_instruction": {
                "parts": [
                    {
                        "text": _build_system_prompt(payload, language, entries),
                    }
                ]
            },
            "contents": [
                {
                    "role": "model" if message["role"] == "assistant" else "user",
                    "parts": [
                        {
                            "text": message["content"],
                        }
                    ],
                }
                for message in messages
            ],
        },
        headers={
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
        timeout=settings.AGRI_BOT_TIMEOUT_SECONDS,
    )
    return {
        "answer": _extract_gemini_text(response),
        "provider_name": "gemini",
        "provider_label": "Google Gemini",
        "model": settings.GEMINI_MODEL,
    }


def _fallback_answer(entries: list[dict], language: str, context: dict) -> str:
    if entries:
        primary_answer = _localized_answer(entries[0], language)
        if len(entries) == 1:
            return primary_answer

        secondary_answer = _localized_answer(entries[1], language)
        if secondary_answer == primary_answer:
            return primary_answer
        return f"{primary_answer}\n\nAlso consider this related guidance: {secondary_answer}"

    crop = context.get("crop")
    disease_name = context.get("disease_name")
    topic_line = ""
    if crop and disease_name:
        topic_line = f" Current context: crop={crop}, disease={disease_name}."
    elif crop:
        topic_line = f" Current crop context: {crop}."
    elif disease_name:
        topic_line = f" Current disease context: {disease_name}."

    generic_answers = {
        "en": (
            "I can help with crop planning, irrigation timing, disease symptoms, soil health, and market timing."
            " Share the crop name, growth stage, symptoms, weather, or recent field changes so I can guide you more precisely."
        ),
        "hi": (
            "Main fasal chayan, sinchai samay, rog ke lakshan, mitti ki sehat aur market timing par madad kar sakta hoon."
            " Kripya fasal ka naam, growth stage, lakshan, mausam ya haal ki field changes batayen taaki main zyada sahi salah de sakoon."
        ),
        "ta": (
            "Naan payir therivu, neerpaasan neram, noi arikurigal, mann aarokkiyam, matrum market timing kurithu udhavi seiya mudiyum."
            " Daya seithu payir peyar, growth stage, arikurigal, weather, allathu recent field changes share pannunga; appo naan innum thelivana vazhikaattal kudukka mudiyum."
        ),
    }
    return generic_answers.get(language, generic_answers["en"]) + topic_line


def _build_follow_ups(entries: list[dict], context: dict) -> list[str]:
    suggestions: list[str] = []
    for entry in entries:
        for suggestion in entry.get("follow_ups", []):
            suggestion_text = _clean_text(suggestion)
            if suggestion_text and suggestion_text not in suggestions:
                suggestions.append(suggestion_text)

    if context.get("crop"):
        crop_suggestion = f"How can I improve {context['crop']} performance this week?"
        if crop_suggestion not in suggestions:
            suggestions.append(crop_suggestion)
    if context.get("disease_name"):
        disease_suggestion = f"What should I monitor next for {context['disease_name']}?"
        if disease_suggestion not in suggestions:
            suggestions.append(disease_suggestion)

    generic_pool = [
        "What should I inspect in the field next?",
        "Can you explain this in simpler farmer-friendly language?",
        "What is the safest next step if the condition worsens?",
    ]
    for suggestion in generic_pool:
        if suggestion not in suggestions:
            suggestions.append(suggestion)

    return suggestions[:4]


def answer_farmer_question(payload: dict) -> dict:
    messages = _normalize_messages(payload)
    language = _normalize_language(payload.get("language"))
    context = _context_from_payload(payload)
    selected_entries = _select_entries(payload, messages)
    provider_selection = _resolve_provider(payload.get("provider"))

    answer = None
    provider_notice = provider_selection["notice"]
    provider_name = "local"
    provider_label = "Local Agriculture Fallback"
    model = None
    response_mode = "fallback"

    try:
        if provider_selection["active"] == "openai":
            provider_result = _call_openai(messages, payload, language, selected_entries)
            answer = provider_result["answer"]
            provider_name = provider_result["provider_name"]
            provider_label = provider_result["provider_label"]
            model = provider_result["model"]
            response_mode = "provider"
        elif provider_selection["active"] == "gemini":
            provider_result = _call_gemini(messages, payload, language, selected_entries)
            answer = provider_result["answer"]
            provider_name = provider_result["provider_name"]
            provider_label = provider_result["provider_label"]
            model = provider_result["model"]
            response_mode = "provider"
    except ProviderRequestError as exc:
        provider_notice = str(exc)

    if not answer:
        answer = _fallback_answer(selected_entries, language, context)

    configured_providers = _configured_providers()
    if response_mode == "provider":
        knowledge_source = (
            "External AI response grounded with bundled agriculture notes and current module outputs."
        )
    else:
        knowledge_source = "Bundled agriculture knowledge base with local fallback reasoning."

    return {
        "language": language,
        "answer": answer,
        "follow_up_suggestions": _build_follow_ups(selected_entries, context),
        "knowledge_source": knowledge_source,
        "provider_name": provider_name,
        "provider_label": provider_label,
        "model": model,
        "response_mode": response_mode,
        "provider_notice": provider_notice,
        "configured_providers": configured_providers,
    }
