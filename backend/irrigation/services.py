from irrigation.model import artifact_exists, get_model_path, load_artifact
from irrigation.weather import WeatherLookupError, fetch_live_weather


BASE_WATER_REQUIREMENT_MM = {
    "rice": 9.0,
    "cotton": 6.2,
    "maize": 5.5,
    "wheat": 4.8,
    "groundnut": 4.3,
}

STAGE_MULTIPLIER = {
    "seedling": 0.75,
    "vegetative": 1.0,
    "flowering": 1.2,
    "harvest": 0.6,
}


def _resolve_weather_inputs(payload: dict) -> tuple[dict, dict]:
    resolved_payload = dict(payload)
    weather_summary = {
        "status": "manual",
        "source": "Manual form input",
        "location": payload.get("location"),
        "condition": None,
    }

    if payload.get("use_live_weather") and payload.get("location"):
        try:
            live_weather = fetch_live_weather(payload["location"])
            resolved_payload["temperature_c"] = live_weather["temperature_c"]
            resolved_payload["humidity_pct"] = live_weather["humidity_pct"]
            if resolved_payload.get("rainfall_forecast_mm") is None:
                resolved_payload["rainfall_forecast_mm"] = live_weather["observed_rain_mm"]

            weather_summary = {
                "status": "live",
                "source": live_weather["source"],
                "location": live_weather["location_label"],
                "condition": live_weather["condition"],
                "temperature_c": live_weather["temperature_c"],
                "humidity_pct": live_weather["humidity_pct"],
                "rainfall_signal_mm": resolved_payload["rainfall_forecast_mm"],
                "wind_speed_mps": live_weather["wind_speed_mps"],
                "note": (
                    "Temperature and humidity were pulled from live weather data. "
                    "Rainfall uses your manual forecast when supplied, otherwise the recent observed rain signal."
                ),
            }
        except WeatherLookupError as exc:
            weather_summary = {
                "status": "manual_fallback",
                "source": "Manual form input",
                "location": payload.get("location"),
                "condition": None,
                "note": str(exc),
            }

    required_fields = ("temperature_c", "humidity_pct", "rainfall_forecast_mm")
    missing_fields = [field for field in required_fields if resolved_payload.get(field) is None]
    if missing_fields:
        raise ValueError(
            "Missing weather inputs: "
            + ", ".join(missing_fields)
            + ". Provide them manually or enable live weather with a valid location and API key."
        )

    return resolved_payload, weather_summary


def _heuristic_water_depth(payload: dict) -> float:
    crop_key = payload["crop"].strip().lower()
    base_mm = BASE_WATER_REQUIREMENT_MM.get(crop_key, 5.0)
    stage_factor = STAGE_MULTIPLIER.get(payload["growth_stage"].strip().lower(), 1.0)

    temperature_factor = 1.15 if payload["temperature_c"] >= 32 else 1.0
    humidity_factor = 0.9 if payload["humidity_pct"] >= 70 else 1.0
    rainfall_offset = payload["rainfall_forecast_mm"] * 0.65
    soil_moisture_offset = max(0.0, (payload["soil_moisture_pct"] - 30) * 0.12)

    return max(
        0.0,
        (base_mm * stage_factor * temperature_factor * humidity_factor)
        - rainfall_offset
        - soil_moisture_offset,
    )


def _recommendation_window(payload: dict, water_depth_mm: float) -> str:
    if water_depth_mm <= 1.0:
        return "Skip irrigation for the next 24 hours and review after the next forecast update."
    if payload["rainfall_forecast_mm"] >= 8:
        return "Irrigate lightly tomorrow morning between 06:00 and 08:00."
    if payload["temperature_c"] >= 34:
        return "Irrigate early tomorrow between 05:00 and 06:30 to reduce evaporation loss."
    return "Irrigate in the next morning window between 05:30 and 07:30."


def create_irrigation_plan(payload: dict) -> dict:
    resolved_payload, weather_summary = _resolve_weather_inputs(payload)

    artifact = load_artifact()
    if artifact is not None:
        defaults = artifact.feature_defaults
        feature_row = {
            "crop": resolved_payload.get("crop")
            if resolved_payload.get("crop") is not None
            else defaults["crop"],
            "growth_stage": resolved_payload.get("growth_stage")
            if resolved_payload.get("growth_stage") is not None
            else defaults["growth_stage"],
            "soil_moisture_pct": resolved_payload.get("soil_moisture_pct")
            if resolved_payload.get("soil_moisture_pct") is not None
            else defaults["soil_moisture_pct"],
            "rainfall_forecast_mm": resolved_payload.get("rainfall_forecast_mm")
            if resolved_payload.get("rainfall_forecast_mm") is not None
            else defaults["rainfall_forecast_mm"],
            "temperature_c": resolved_payload.get("temperature_c")
            if resolved_payload.get("temperature_c") is not None
            else defaults["temperature_c"],
            "humidity_pct": resolved_payload.get("humidity_pct")
            if resolved_payload.get("humidity_pct") is not None
            else defaults["humidity_pct"],
            "area_hectares": resolved_payload.get("area_hectares")
            if resolved_payload.get("area_hectares") is not None
            else defaults["area_hectares"],
        }
        water_depth_mm = max(0.0, float(artifact.pipeline.predict([feature_row])[0]))
        model_family = artifact.model_family
        model_status = "trained"
    else:
        water_depth_mm = _heuristic_water_depth(resolved_payload)
        model_family = "Rule-based fallback until a trained Random Forest model is added"
        model_status = "fallback"

    crop_key = resolved_payload["crop"].strip().lower()
    base_mm = BASE_WATER_REQUIREMENT_MM.get(crop_key, 5.0)
    stage_factor = STAGE_MULTIPLIER.get(resolved_payload["growth_stage"].strip().lower(), 1.0)
    total_water_liters = round(water_depth_mm * resolved_payload["area_hectares"] * 10000, 2)
    irrigation_needed = water_depth_mm > 1.0
    recommended_window = _recommendation_window(resolved_payload, water_depth_mm)

    rationale = [
        f"Base crop water need for {resolved_payload['crop']} was estimated at {base_mm:.1f} mm.",
        f"Growth stage '{resolved_payload['growth_stage']}' applied a multiplier of {stage_factor:.2f}.",
        (
            f"Rainfall signal of {resolved_payload['rainfall_forecast_mm']:.1f} mm was used to reduce irrigation demand."
        ),
        (
            f"Soil moisture at {resolved_payload['soil_moisture_pct']:.1f}% and humidity at "
            f"{resolved_payload['humidity_pct']:.1f}% were factored into the decision."
        ),
    ]
    if weather_summary.get("note"):
        rationale.append(weather_summary["note"])

    return {
        "irrigation_needed": irrigation_needed,
        "recommended_window": recommended_window,
        "water_depth_mm": round(water_depth_mm, 2),
        "total_water_liters": total_water_liters,
        "rationale": rationale,
        "model_family": model_family,
        "model_status": model_status,
        "model_path": str(get_model_path()) if artifact_exists() else None,
        "weather_summary": weather_summary,
        "applied_inputs": {
            "crop": resolved_payload["crop"],
            "growth_stage": resolved_payload["growth_stage"],
            "soil_moisture_pct": resolved_payload["soil_moisture_pct"],
            "rainfall_forecast_mm": resolved_payload["rainfall_forecast_mm"],
            "temperature_c": resolved_payload["temperature_c"],
            "humidity_pct": resolved_payload["humidity_pct"],
            "area_hectares": resolved_payload["area_hectares"],
        },
    }
