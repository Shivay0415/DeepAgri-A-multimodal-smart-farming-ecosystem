from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "disease_classifier.keras"
METADATA_PATH = MODEL_DIR / "disease_classifier_metadata.json"


@dataclass(frozen=True)
class DiseaseArtifact:
    model: Any
    class_names: list[str]
    image_size: tuple[int, int]
    model_family: str


_artifact_cache: DiseaseArtifact | None = None


def artifact_exists() -> bool:
    return MODEL_PATH.exists() and METADATA_PATH.exists()


def get_model_path() -> Path:
    return MODEL_PATH


def clear_artifact_cache() -> None:
    global _artifact_cache
    _artifact_cache = None


def load_artifact() -> DiseaseArtifact | None:
    global _artifact_cache
    if _artifact_cache is not None:
        return _artifact_cache

    if not artifact_exists():
        return None

    try:
        import tensorflow as tf
    except ImportError:
        return None

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    model = tf.keras.models.load_model(MODEL_PATH)
    image_size = metadata.get("image_size", [224, 224])

    _artifact_cache = DiseaseArtifact(
        model=model,
        class_names=list(metadata["class_names"]),
        image_size=(int(image_size[0]), int(image_size[1])),
        model_family=str(
            metadata.get("model_family", "Trained MobileNetV2 disease classifier")
        ),
    )
    return _artifact_cache
