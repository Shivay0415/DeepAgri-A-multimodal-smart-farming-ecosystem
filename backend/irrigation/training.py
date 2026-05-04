from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

from irrigation.model import MODEL_DIR, MODEL_PATH, clear_artifact_cache


NUMERIC_FIELDS = [
    "soil_moisture_pct",
    "rainfall_forecast_mm",
    "temperature_c",
    "humidity_pct",
    "area_hectares",
]

CATEGORICAL_FIELDS = ["crop", "growth_stage"]
FEATURE_FIELDS = [*CATEGORICAL_FIELDS, *NUMERIC_FIELDS]

COLUMN_ALIASES = {
    "crop": ["crop", "Crop", "crop_name", "Crop_Name"],
    "growth_stage": ["growth_stage", "Growth_Stage", "stage", "Stage"],
    "soil_moisture_pct": [
        "soil_moisture_pct",
        "Soil_Moisture",
        "soil_moisture",
        "Soil_Moisture_Pct",
    ],
    "rainfall_forecast_mm": [
        "rainfall_forecast_mm",
        "Rainfall_mm",
        "rainfall_mm",
        "Rainfall",
    ],
    "temperature_c": ["temperature_c", "Temperature_C", "temperature", "Temperature"],
    "humidity_pct": ["humidity_pct", "Humidity", "humidity"],
    "area_hectares": ["area_hectares", "Area_Hectares", "area", "Area"],
    "target_water_depth_mm": [
        "target_water_depth_mm",
        "Target_Water_Depth_mm",
        "Water_Depth_mm",
    ],
    "irrigation_need": ["Irrigation_Need", "irrigation_need", "Need_Level"],
}

DEFAULT_FEATURE_VALUES: dict[str, float | str] = {
    "crop": "generic",
    "growth_stage": "vegetative",
    "area_hectares": 1.0,
}


def _resolve_column(fieldnames: list[str], canonical_name: str) -> str | None:
    for candidate in COLUMN_ALIASES[canonical_name]:
        if candidate in fieldnames:
            return candidate
    return None


def _load_reader(dataset_path: Path) -> tuple[list[str], list[dict]]:
    with dataset_path.open("r", encoding="utf-8", newline="") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if reader.fieldnames is None:
            raise ValueError("Dataset must include a header row.")
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if not rows:
        raise ValueError("Dataset must contain at least one training row.")
    return fieldnames, rows


def _detect_prediction_kind(fieldnames: list[str]) -> str:
    if _resolve_column(fieldnames, "target_water_depth_mm"):
        return "regressor"
    if _resolve_column(fieldnames, "irrigation_need"):
        return "classifier"
    raise ValueError(
        "Dataset must include either 'target_water_depth_mm' for a regressor or "
        "'Irrigation_Need' for a classifier."
    )


def _string_value(row: dict, column_name: str | None, default: str) -> str:
    if not column_name:
        return default
    value = str(row.get(column_name, "")).strip().lower()
    return value or default


def _float_value(
    row: dict,
    column_name: str | None,
    *,
    default: float | None = None,
) -> float:
    if not column_name:
        if default is None:
            raise ValueError("Missing required numeric field.")
        return float(default)

    raw_value = row.get(column_name)
    if raw_value in (None, ""):
        if default is None:
            raise ValueError("Missing required numeric field.")
        return float(default)
    return float(raw_value)


def _feature_defaults(rows: list[dict]) -> dict[str, float | str]:
    defaults: dict[str, float | str] = {}
    for field in NUMERIC_FIELDS:
        defaults[field] = round(sum(float(row[field]) for row in rows) / len(rows), 4)
    for field in CATEGORICAL_FIELDS:
        defaults[field] = Counter(str(row[field]) for row in rows).most_common(1)[0][0]
    return defaults


def _read_rows(dataset_path: Path) -> tuple[list[dict], str]:
    fieldnames, raw_rows = _load_reader(dataset_path)
    prediction_kind = _detect_prediction_kind(fieldnames)

    column_map = {
        field: _resolve_column(fieldnames, field)
        for field in FEATURE_FIELDS
        + ["target_water_depth_mm", "irrigation_need"]
    }

    required_numeric = [
        "soil_moisture_pct",
        "rainfall_forecast_mm",
        "temperature_c",
        "humidity_pct",
    ]
    missing_numeric = [field for field in required_numeric if column_map[field] is None]
    if missing_numeric:
        raise ValueError(
            "Dataset is missing required irrigation features: " + ", ".join(missing_numeric)
        )

    rows = []
    for index, row in enumerate(raw_rows, start=2):
        try:
            normalized_row = {
                "crop": _string_value(row, column_map["crop"], str(DEFAULT_FEATURE_VALUES["crop"])),
                "growth_stage": _string_value(
                    row,
                    column_map["growth_stage"],
                    str(DEFAULT_FEATURE_VALUES["growth_stage"]),
                ),
                "soil_moisture_pct": _float_value(row, column_map["soil_moisture_pct"]),
                "rainfall_forecast_mm": _float_value(row, column_map["rainfall_forecast_mm"]),
                "temperature_c": _float_value(row, column_map["temperature_c"]),
                "humidity_pct": _float_value(row, column_map["humidity_pct"]),
                "area_hectares": _float_value(
                    row,
                    column_map["area_hectares"],
                    default=float(DEFAULT_FEATURE_VALUES["area_hectares"]),
                ),
            }

            if prediction_kind == "regressor":
                normalized_row["target_water_depth_mm"] = _float_value(
                    row,
                    column_map["target_water_depth_mm"],
                )
            else:
                target_label = _string_value(row, column_map["irrigation_need"], "")
                if not target_label:
                    raise ValueError("Classifier target label is empty.")
                normalized_row["irrigation_need"] = target_label
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid value in irrigation dataset row {index}.") from exc

        rows.append(normalized_row)

    return rows, prediction_kind


def train_irrigation_model(dataset_path: Path) -> dict:
    rows, prediction_kind = _read_rows(dataset_path)
    features = [{field: row[field] for field in FEATURE_FIELDS} for row in rows]

    if prediction_kind == "classifier":
        targets = [row["irrigation_need"] for row in rows]
        pipeline = Pipeline(
            steps=[
                ("vectorizer", DictVectorizer(sparse=False)),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=100,
                        random_state=42,
                    ),
                ),
            ]
        )
        model_family = "Notebook-inspired Random Forest Classifier"
        target_labels = sorted({str(target) for target in targets})
    else:
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
        model_family = "Trained Random Forest Regressor"
        target_labels = None

    pipeline.fit(features, targets)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_defaults": _feature_defaults(rows),
            "model_family": model_family,
            "prediction_kind": prediction_kind,
            "target_labels": target_labels,
        },
        MODEL_PATH,
    )
    clear_artifact_cache()

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(MODEL_PATH),
        "samples": len(rows),
        "prediction_kind": prediction_kind,
        "target_labels": target_labels,
    }
