from dataclasses import dataclass

from crop.model import artifact_exists, get_model_path, load_artifact


@dataclass(frozen=True)
class CropProfile:
    name: str
    nitrogen: float
    phosphorus: float
    potassium: float
    ph_min: float
    ph_max: float
    notes: tuple[str, str]


CROP_PROFILES = (
    CropProfile(
        "cotton",
        80,
        45,
        40,
        5.5,
        7.5,
        (
            "Moderate nitrogen demand fits many field conditions.",
            "Performs well in slightly acidic to neutral soils.",
        ),
    ),
    CropProfile(
        "rice",
        95,
        40,
        40,
        5.0,
        6.5,
        (
            "Thrives in water-rich environments.",
            "Benefits from higher nitrogen availability.",
        ),
    ),
    CropProfile(
        "maize",
        70,
        35,
        35,
        5.8,
        7.0,
        (
            "Balanced NPK requirement.",
            "Suitable for neutral pH bands.",
        ),
    ),
    CropProfile(
        "wheat",
        60,
        30,
        25,
        6.0,
        7.5,
        (
            "Prefers moderate fertility.",
            "Stable option for neutral soil chemistry.",
        ),
    ),
    CropProfile(
        "groundnut",
        25,
        45,
        55,
        5.8,
        7.0,
        (
            "Needs stronger phosphorus and potassium support.",
            "Does not require very high nitrogen levels.",
        ),
    ),
)


def _profile_score(profile: CropProfile, payload: dict) -> tuple[float, list[str]]:
    nutrient_gap = (
        abs(payload["nitrogen"] - profile.nitrogen)
        + abs(payload["phosphorus"] - profile.phosphorus)
        + abs(payload["potassium"] - profile.potassium)
    )

    soil_ph = payload["ph"]
    if profile.ph_min <= soil_ph <= profile.ph_max:
        ph_penalty = 0.0
        ph_reason = f"Soil pH {soil_ph:.1f} fits the preferred range for {profile.name}."
    else:
        delta = min(abs(soil_ph - profile.ph_min), abs(soil_ph - profile.ph_max))
        ph_penalty = delta * 20
        ph_reason = (
            f"Soil pH {soil_ph:.1f} is slightly outside the ideal range for {profile.name}."
        )

    climate_bonus = 0.0
    climate_reason = "Climate context is neutral because no strong external signal was provided."
    temperature = payload.get("temperature_c")
    rainfall = payload.get("rainfall_mm")

    if temperature is not None:
        if 24 <= temperature <= 33 and profile.name in {"cotton", "rice", "maize"}:
            climate_bonus = 12.0
            climate_reason = "Temperature profile supports a warm-season crop."
        elif temperature < 22 and profile.name == "wheat":
            climate_bonus = 10.0
            climate_reason = "Temperature profile supports a cooler-season crop."

    if rainfall is not None:
        if rainfall >= 120 and profile.name == "rice":
            climate_bonus += 10.0
            climate_reason = "Rainfall estimate favors a water-intensive crop."
        elif rainfall < 60 and profile.name in {"cotton", "groundnut"}:
            climate_bonus += 8.0
            climate_reason = "Lower rainfall estimate favors relatively drier crop choices."

    score = nutrient_gap + ph_penalty - climate_bonus
    reasons = [profile.notes[0], profile.notes[1], ph_reason, climate_reason]
    return score, reasons


def recommend_crop(payload: dict) -> dict:
    artifact = load_artifact()
    if artifact is not None:
        feature_values = []
        for feature_name in artifact.feature_order:
            raw_value = payload.get(feature_name)
            if raw_value is None:
                raw_value = artifact.feature_defaults[feature_name]
            feature_values.append(raw_value)

        probabilities = artifact.pipeline.predict_proba([feature_values])[0]
        class_labels = list(artifact.pipeline.classes_)
        ranked_probabilities = sorted(
            zip(class_labels, probabilities),
            key=lambda item: item[1],
            reverse=True,
        )

        top_predictions = []
        for crop_name, probability in ranked_probabilities[:3]:
            top_predictions.append(
                {
                    "crop": crop_name,
                    "confidence": round(float(probability), 2),
                    "rationale": [
                        "Prediction generated from the trained crop recommendation model.",
                        f"Missing climate inputs use training-set defaults stored with the model artifact.",
                    ],
                }
            )

        return {
            "recommended_crop": top_predictions[0]["crop"],
            "confidence": top_predictions[0]["confidence"],
            "top_predictions": top_predictions,
            "model_family": artifact.model_family,
            "model_status": "trained",
            "model_path": str(get_model_path()),
        }

    ranked: list[tuple[float, CropProfile, list[str]]] = []
    for profile in CROP_PROFILES:
        score, reasons = _profile_score(profile, payload)
        ranked.append((score, profile, reasons))

    ranked.sort(key=lambda item: item[0])
    best_score = ranked[0][0]

    top_predictions = []
    for score, profile, reasons in ranked[:3]:
        confidence = max(0.51, min(0.95, 1 - ((score - best_score) / 180) - 0.1))
        top_predictions.append(
            {
                "crop": profile.name,
                "confidence": round(confidence, 2),
                "rationale": reasons,
            }
        )

    return {
        "recommended_crop": top_predictions[0]["crop"],
        "confidence": top_predictions[0]["confidence"],
        "top_predictions": top_predictions,
        "model_family": "Rule-based fallback until a trained DNN/TabNet model is added",
        "model_status": "fallback",
        "model_path": str(get_model_path()) if artifact_exists() else None,
    }
