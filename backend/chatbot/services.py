import json
from functools import lru_cache
from pathlib import Path


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "data" / "agri_knowledge_base.json"


@lru_cache(maxsize=1)
def _load_knowledge_base() -> list[dict]:
    with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as knowledge_file:
        return json.load(knowledge_file)


def _score_entry(entry: dict, signal: str) -> int:
    score = 0
    for keyword in entry["keywords"]:
        if keyword.lower() in signal:
            score += 2
    return score


def _select_entry(payload: dict) -> dict | None:
    signal = " ".join(
        value.lower()
        for value in [
            payload["question"],
            payload.get("crop") or "",
            payload.get("disease_name") or "",
        ]
    )

    best_entry = None
    best_score = 0
    for entry in _load_knowledge_base():
        score = _score_entry(entry, signal)
        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry


def _localized_answer(entry: dict, language: str) -> str:
    key = {
        "en": "answer_en",
        "hi": "answer_hi",
        "ta": "answer_ta",
    }.get(language, "answer_en")
    return entry.get(key) or entry["answer_en"]


def answer_farmer_question(payload: dict) -> dict:
    language = payload.get("language", "en").lower()
    if language not in {"en", "hi", "ta"}:
        language = "en"

    entry = _select_entry(payload)
    if entry is None:
        answer = (
            "I can help explain crop stress, irrigation timing, disease remedies, and market "
            "planning. Add the crop name or disease name for a more specific answer."
        )
        follow_ups = [
            "Share the crop name and growth stage.",
            "Upload a leaf photo if symptoms are visible.",
            "Ask for an organic remedy or irrigation-specific explanation.",
        ]
    else:
        answer = _localized_answer(entry, language)
        follow_ups = list(entry["follow_ups"])

    return {
        "language": language,
        "answer": answer,
        "follow_up_suggestions": follow_ups,
        "knowledge_source": "Bundled agriculture knowledge base with RAG-style dataset matching",
    }
