from __future__ import annotations

import csv
from pathlib import Path

import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from crop.deep_training import train_notebook_model
from crop.model import MODEL_DIR, MODEL_PATH, clear_artifact_cache


COLUMN_ALIASES = {
    "nitrogen": ("nitrogen", "N", "n"),
    "phosphorus": ("phosphorus", "P", "p"),
    "potassium": ("potassium", "K", "k"),
    "temperature_c": ("temperature_c", "temperature"),
    "humidity_pct": ("humidity_pct", "humidity"),
    "ph": ("ph",),
    "rainfall_mm": ("rainfall_mm", "rainfall"),
    "label": ("label",),
}


def _read_rows(dataset_path: Path) -> list[dict]:
    with dataset_path.open("r", encoding="utf-8", newline="") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if reader.fieldnames is None:
            raise ValueError("Dataset must include a header row.")

        def resolve_column(canonical_name: str) -> str | None:
            for candidate in COLUMN_ALIASES[canonical_name]:
                if candidate in reader.fieldnames:
                    return candidate
            return None

        resolved_columns: dict[str, str] = {}
        missing = []
        for canonical_name in COLUMN_ALIASES:
            resolved = resolve_column(canonical_name)
            if resolved is None:
                missing.append(canonical_name)
            else:
                resolved_columns[canonical_name] = resolved

        if missing:
            raise ValueError("Dataset is missing required columns: " + ", ".join(sorted(missing)))

        rows = []
        for index, row in enumerate(reader, start=2):
            try:
                rows.append(
                    {
                        "nitrogen": float(row[resolved_columns["nitrogen"]]),
                        "phosphorus": float(row[resolved_columns["phosphorus"]]),
                        "potassium": float(row[resolved_columns["potassium"]]),
                        "temperature_c": float(row[resolved_columns["temperature_c"]]),
                        "humidity_pct": float(row[resolved_columns["humidity_pct"]]),
                        "ph": float(row[resolved_columns["ph"]]),
                        "rainfall_mm": float(row[resolved_columns["rainfall_mm"]]),
                        "label": str(row[resolved_columns["label"]]).strip().lower(),
                    }
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value in dataset row {index}.") from exc

    if not rows:
        raise ValueError("Dataset must contain at least one training row.")
    return rows


def train_crop_model(dataset_path: Path, trainer: str = "sklearn-mlp") -> dict:
    rows = _read_rows(dataset_path)
    feature_order = [
        "nitrogen",
        "phosphorus",
        "potassium",
        "temperature_c",
        "humidity_pct",
        "ph",
        "rainfall_mm",
    ]
    labels = [row["label"] for row in rows]

    if trainer in {"notebook-mlp", "notebook-transformer"}:
        artifact_payload, training_summary = train_notebook_model(
            rows=rows,
            feature_order=feature_order,
            architecture=trainer,
        )
    else:
        features = [[row[name] for name in feature_order] for row in rows]
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
        artifact_payload = {
            "artifact_type": "sklearn",
            "pipeline": pipeline,
            "labels": sorted(set(labels)),
            "feature_order": feature_order,
            "feature_defaults": feature_defaults,
            "model_family": "Trained DNN-style MLP classifier",
        }
        training_summary = {"trainer": trainer, "validation_accuracy": None}

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact_payload, MODEL_PATH)
    clear_artifact_cache()

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(MODEL_PATH),
        "samples": len(rows),
        "classes": sorted(set(labels)),
        "trainer": training_summary["trainer"],
        "validation_accuracy": training_summary.get("validation_accuracy"),
    }
