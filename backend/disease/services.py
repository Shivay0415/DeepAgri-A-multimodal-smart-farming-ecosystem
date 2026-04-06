import json
from functools import lru_cache
from pathlib import Path


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "disease_catalog.json"


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict]:
    with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def analyze_leaf_image(
    *,
    filename: str,
    image_size_bytes: int,
    crop: str,
    symptom_hint: str | None,
) -> dict:
    signal = f"{filename} {symptom_hint or ''}".lower()
    crop_key = crop.strip().lower()

    best_match = None
    best_score = 0
    matched_keywords: list[str] = []

    for entry in _load_catalog():
        entry_crop = entry["crop"].lower()
        score = 0
        entry_matches: list[str] = []

        if entry_crop == crop_key:
            score += 2
        elif entry_crop != "generic":
            continue

        for keyword in entry["keywords"]:
            if keyword.lower() in signal:
                score += 2
                entry_matches.append(keyword)

        if score > best_score:
            best_score = score
            best_match = entry
            matched_keywords = entry_matches

    if best_match is None or best_score == 0:
        return {
            "crop": crop,
            "disease_name": "Healthy or Unclassified Condition",
            "confidence": 0.62,
            "severity": "low",
            "remedies": [
                "Capture a closer image in good daylight for better disease classification.",
                "Include a symptom hint such as spots, curling, or yellowing.",
                "Track changes over the next few days and compare multiple leaves.",
            ],
            "notes": [
                f"Image size received: {image_size_bytes} bytes.",
                "The current service uses a dataset-backed symptom matcher and does not evaluate image pixels yet.",
            ],
            "model_family": "Dataset-backed symptom matcher placeholder for a CNN pipeline",
        }

    confidence = min(
        0.97,
        round(best_match["confidence_base"] + (0.02 * len(matched_keywords)), 2),
    )

    notes = list(best_match["notes"])
    if matched_keywords:
        notes.append("Matched keywords: " + ", ".join(matched_keywords))
    notes.append(
        "This is a dataset-backed symptom match. Replace with a CNN pipeline for full image inference."
    )

    return {
        "crop": crop,
        "disease_name": best_match["disease_name"],
        "confidence": confidence,
        "severity": best_match["severity"],
        "remedies": list(best_match["remedies"]),
        "notes": notes,
        "model_family": "Dataset-backed symptom matcher placeholder for a CNN pipeline",
    }
