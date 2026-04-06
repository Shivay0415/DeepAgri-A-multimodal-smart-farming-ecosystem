from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

from irrigation.model import MODEL_DIR, MODEL_PATH, clear_artifact_cache


REQUIRED_COLUMNS = {
    "crop",
    "growth_stage",
    "soil_moisture_pct",
    "rainfall_forecast_mm",
    "temperature_c",
    "humidity_pct",
    "area_hectares",
    "target_water_depth_mm",
}

NUMERIC_FIELDS = [
    "soil_moisture_pct",
    "rainfall_forecast_mm",
    "temperature_c",
    "humidity_pct",
    "area_hectares",
]

CATEGORICAL_FIELDS = ["crop", "growth_stage"]


def _read_rows(dataset_path: Path) -> list[dict]:
    with dataset_path.open("r", encoding="utf-8", newline="") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if reader.fieldnames is None:
            raise ValueError("Dataset must include a header row.")

        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                "Dataset is missing required columns: " + ", ".join(sorted(missing))
            )

        rows = []
        for index, row in enumerate(reader, start=2):
            try:
                rows.append(
                    {
                        "crop": str(row["crop"]).strip().lower(),
                        "growth_stage": str(row["growth_stage"]).strip().lower(),
                        "soil_moisture_pct": float(row["soil_moisture_pct"]),
                        "rainfall_forecast_mm": float(row["rainfall_forecast_mm"]),
                        "temperature_c": float(row["temperature_c"]),
                        "humidity_pct": float(row["humidity_pct"]),
                        "area_hectares": float(row["area_hectares"]),
                        "target_water_depth_mm": float(row["target_water_depth_mm"]),
                    }
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid value in irrigation dataset row {index}.") from exc

    if not rows:
        raise ValueError("Dataset must contain at least one training row.")
    return rows


def _feature_defaults(rows: list[dict]) -> dict[str, float | str]:
    defaults: dict[str, float | str] = {}
    for field in NUMERIC_FIELDS:
        defaults[field] = round(sum(row[field] for row in rows) / len(rows), 4)
    for field in CATEGORICAL_FIELDS:
        defaults[field] = Counter(row[field] for row in rows).most_common(1)[0][0]
    return defaults


def train_irrigation_model(dataset_path: Path) -> dict:
    rows = _read_rows(dataset_path)
    features = [
        {
            "crop": row["crop"],
            "growth_stage": row["growth_stage"],
            "soil_moisture_pct": row["soil_moisture_pct"],
            "rainfall_forecast_mm": row["rainfall_forecast_mm"],
            "temperature_c": row["temperature_c"],
            "humidity_pct": row["humidity_pct"],
            "area_hectares": row["area_hectares"],
        }
        for row in rows
    ]
    targets = [row["target_water_depth_mm"] for row in rows]

    pipeline = Pipeline(
        steps=[
            ("vectorizer", DictVectorizer(sparse=False)),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=250,
                    random_state=42,
                    min_samples_leaf=2,
                ),
            ),
        ]
    )
    pipeline.fit(features, targets)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_defaults": _feature_defaults(rows),
            "model_family": "Trained Random Forest Regressor",
        },
        MODEL_PATH,
    )
    clear_artifact_cache()

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(MODEL_PATH),
        "samples": len(rows),
    }

