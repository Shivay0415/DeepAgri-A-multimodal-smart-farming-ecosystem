from __future__ import annotations

import csv
from pathlib import Path

import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from crop.model import MODEL_DIR, MODEL_PATH, clear_artifact_cache


REQUIRED_COLUMNS = {
    "nitrogen",
    "phosphorus",
    "potassium",
    "ph",
    "temperature_c",
    "rainfall_mm",
    "label",
}


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
                        "nitrogen": float(row["nitrogen"]),
                        "phosphorus": float(row["phosphorus"]),
                        "potassium": float(row["potassium"]),
                        "ph": float(row["ph"]),
                        "temperature_c": float(row["temperature_c"]),
                        "rainfall_mm": float(row["rainfall_mm"]),
                        "label": str(row["label"]).strip().lower(),
                    }
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value in dataset row {index}.") from exc

    if not rows:
        raise ValueError("Dataset must contain at least one training row.")
    return rows


def train_crop_model(dataset_path: Path) -> dict:
    rows = _read_rows(dataset_path)
    feature_order = [
        "nitrogen",
        "phosphorus",
        "potassium",
        "ph",
        "temperature_c",
        "rainfall_mm",
    ]
    features = [[row[name] for name in feature_order] for row in rows]
    labels = [row["label"] for row in rows]

    feature_defaults = {
        name: round(sum(row[name] for row in rows) / len(rows), 4) for name in feature_order
    }

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    solver="adam",
                    learning_rate_init=0.001,
                    max_iter=1200,
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(features, labels)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "labels": sorted(set(labels)),
            "feature_order": feature_order,
            "feature_defaults": feature_defaults,
            "model_family": "Trained DNN-style MLP classifier",
        },
        MODEL_PATH,
    )
    clear_artifact_cache()

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(MODEL_PATH),
        "samples": len(rows),
        "classes": sorted(set(labels)),
    }

