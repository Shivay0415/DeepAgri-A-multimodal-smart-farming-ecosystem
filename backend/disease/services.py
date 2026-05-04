import json
from functools import lru_cache
from pathlib import Path

from disease.model import artifact_exists, get_model_path, load_artifact


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "disease_catalog.json"


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict]:
    with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def _catalog_match(signal: str, crop_key: str) -> tuple[dict | None, int, list[str]]:
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

    return best_match, best_score, matched_keywords


def _fallback_response(
    *,
    filename: str,
    image_size_bytes: int,
    crop: str,
    symptom_hint: str | None,
) -> dict:
    signal = f"{filename} {symptom_hint or ''}".lower()
    crop_key = crop.strip().lower()
    best_match, best_score, matched_keywords = _catalog_match(signal, crop_key)

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
                "The current fallback matcher used filename and symptom hints because no trained CNN prediction was available for this image.",
            ],
            "model_family": "Dataset-backed disease fallback",
            "model_status": "fallback",
            "model_path": str(get_model_path()) if artifact_exists() else None,
        }

    confidence = min(
        0.97,
        round(best_match["confidence_base"] + (0.02 * len(matched_keywords)), 2),
    )

    notes = list(best_match["notes"])
    if matched_keywords:
        notes.append("Matched keywords: " + ", ".join(matched_keywords))
    notes.append(
        "This response came from the symptom-and-catalog fallback layer."
    )

    return {
        "crop": crop,
        "disease_name": best_match["disease_name"],
        "confidence": confidence,
        "severity": best_match["severity"],
        "remedies": list(best_match["remedies"]),
        "notes": notes,
        "model_family": "Dataset-backed disease fallback",
        "model_status": "fallback",
        "model_path": str(get_model_path()) if artifact_exists() else None,
    }


def _label_to_crop_and_name(raw_label: str, fallback_crop: str) -> tuple[str, str]:
    if "___" in raw_label:
        crop_name, disease_name = raw_label.split("___", 1)
    elif "__" in raw_label:
        crop_name, disease_name = raw_label.split("__", 1)
    else:
        crop_name, disease_name = fallback_crop, raw_label

    crop_name = crop_name.replace("_", " ").strip() or fallback_crop
    disease_name = disease_name.replace("_", " ").strip() or raw_label
    return crop_name, disease_name


def _severity_from_prediction(disease_name: str, confidence: float) -> str:
    normalized = disease_name.lower()
    if "healthy" in normalized:
        return "low"
    if confidence >= 0.86:
        return "high"
    if confidence >= 0.7:
        return "medium"
    return "low"


def _catalog_remedies(crop_key: str, disease_name: str) -> list[str]:
    disease_name_key = disease_name.lower()
    for entry in _load_catalog():
        if entry["crop"].lower() == crop_key and entry["disease_name"].lower() == disease_name_key:
            return list(entry["remedies"])

    generic_remedies = [
        "Inspect multiple leaves before deciding on treatment.",
        "Isolate badly affected foliage when possible and improve field hygiene.",
        "Use local extension guidance before applying a crop-specific chemical control.",
    ]
    return generic_remedies


def _cnn_response(
    *,
    image_bytes: bytes,
    crop: str,
    symptom_hint: str | None,
) -> dict | None:
    artifact = load_artifact()
    if artifact is None:
        return None

    try:
        import tensorflow as tf
    except ImportError:
        return None

    try:
        decoded = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    except Exception:
        return None

    image_tensor = tf.image.resize(decoded, artifact.image_size)
    image_tensor = tf.cast(image_tensor, tf.float32)
    image_tensor = tf.expand_dims(image_tensor, axis=0)

    probabilities = artifact.model.predict(image_tensor, verbose=0)[0]
    predicted_index = int(tf.math.argmax(probabilities).numpy())
    confidence = round(float(probabilities[predicted_index]), 4)
    raw_label = artifact.class_names[predicted_index]
    predicted_crop, disease_name = _label_to_crop_and_name(raw_label, crop)
    severity = _severity_from_prediction(disease_name, confidence)

    top_indices = sorted(
        range(len(probabilities)),
        key=lambda index: float(probabilities[index]),
        reverse=True,
    )[:3]
    top_predictions = [
        {
            "label": artifact.class_names[index],
            "confidence": round(float(probabilities[index]), 4),
        }
        for index in top_indices
    ]

    notes = [
        f"CNN predicted class '{raw_label}' from pixel-level image features.",
        f"Input symptom hint: {symptom_hint or 'none provided'}.",
    ]
    if predicted_crop.lower() != crop.strip().lower():
        notes.append(
            f"The uploaded image resembles the class crop '{predicted_crop}', while the request crop was '{crop}'."
        )

    return {
        "crop": predicted_crop,
        "disease_name": disease_name,
        "confidence": confidence,
        "severity": severity,
        "remedies": _catalog_remedies(predicted_crop.lower(), disease_name),
        "notes": notes,
        "top_predictions": top_predictions,
        "model_family": artifact.model_family,
        "model_status": "trained",
        "model_path": str(get_model_path()),
    }


def analyze_leaf_image(
    *,
    filename: str,
    image_size_bytes: int,
    image_bytes: bytes,
    crop: str,
    symptom_hint: str | None,
) -> dict:
    cnn_result = _cnn_response(
        image_bytes=image_bytes,
        crop=crop,
        symptom_hint=symptom_hint,
    )
    if cnn_result is not None:
        return cnn_result

    return _fallback_response(
        filename=filename,
        image_size_bytes=image_size_bytes,
        crop=crop,
        symptom_hint=symptom_hint,
    )
