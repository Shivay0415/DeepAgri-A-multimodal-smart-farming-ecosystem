from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib


MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "irrigation_regressor.joblib"


@dataclass(frozen=True)
class IrrigationArtifact:
    pipeline: Any
    feature_defaults: dict[str, float | str]
    model_family: str
    prediction_kind: str
    target_labels: list[str] | None = None


_artifact_cache: IrrigationArtifact | None = None


def artifact_exists() -> bool:
    return MODEL_PATH.exists()


def get_model_path() -> Path:
    return MODEL_PATH


def clear_artifact_cache() -> None:
    global _artifact_cache
    _artifact_cache = None


def load_artifact() -> IrrigationArtifact | None:
    global _artifact_cache
    if _artifact_cache is not None:
        return _artifact_cache

    if not MODEL_PATH.exists():
        return None

    raw = joblib.load(MODEL_PATH)
    target_labels_raw = raw.get("target_labels")
    target_labels = list(target_labels_raw) if target_labels_raw else None
    
    _artifact_cache = IrrigationArtifact(
        pipeline=raw["pipeline"],
        feature_defaults=dict(raw["feature_defaults"]),
        model_family=str(raw.get("model_family", "Trained Irrigation Regressor")),
        prediction_kind=str(raw.get("prediction_kind", "regressor")),
        target_labels=target_labels,
    )
    return _artifact_cache
