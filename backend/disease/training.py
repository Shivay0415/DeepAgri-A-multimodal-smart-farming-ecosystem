from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from disease.model import METADATA_PATH, MODEL_DIR, MODEL_PATH, clear_artifact_cache


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _require_tensorflow():
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ValueError(
            "TensorFlow is required to train Module 3. Install a TensorFlow build compatible with your Python environment before running this command."
        ) from exc
    return tf


def _selected_class_dirs(dataset_path: Path, class_filter: str | None) -> list[Path]:
    class_directories = sorted(path for path in dataset_path.iterdir() if path.is_dir())
    if class_filter:
        filter_text = class_filter.strip().lower()
        class_directories = [
            path for path in class_directories if filter_text in path.name.lower()
        ]

    if len(class_directories) < 2:
        raise ValueError(
            "The disease dataset must contain at least two matching class folders."
        )
    return class_directories


def _copy_subset(
    class_directories: list[Path],
    subset_path: Path,
    max_images_per_class: int,
) -> int:
    total_images = 0
    for class_directory in class_directories:
        target_directory = subset_path / class_directory.name
        target_directory.mkdir(parents=True, exist_ok=True)

        image_files = [
            file_path
            for file_path in sorted(class_directory.iterdir())
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if not image_files:
            continue

        for image_path in image_files[:max_images_per_class]:
            shutil.copy2(image_path, target_directory / image_path.name)
            total_images += 1

    if total_images == 0:
        raise ValueError("No supported images were found in the selected disease classes.")
    return total_images


def train_disease_model(
    dataset_path: Path,
    *,
    class_filter: str | None = None,
    max_images_per_class: int = 800,
    epochs: int = 6,
    batch_size: int = 32,
) -> dict:
    tf = _require_tensorflow()
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise ValueError(f"Dataset path not found: {dataset_path}")

    class_directories = _selected_class_dirs(dataset_path, class_filter)

    with tempfile.TemporaryDirectory(prefix="agri-disease-") as temp_directory:
        subset_path = Path(temp_directory) / "dataset"
        subset_path.mkdir(parents=True, exist_ok=True)

        total_images = _copy_subset(
            class_directories,
            subset_path,
            max_images_per_class=max_images_per_class,
        )

        train_data = tf.keras.utils.image_dataset_from_directory(
            subset_path,
            validation_split=0.2,
            subset="training",
            seed=42,
            image_size=(224, 224),
            batch_size=batch_size,
        )
        validation_data = tf.keras.utils.image_dataset_from_directory(
            subset_path,
            validation_split=0.2,
            subset="validation",
            seed=42,
            image_size=(224, 224),
            batch_size=batch_size,
        )

        class_names = list(train_data.class_names)
        autotune = tf.data.AUTOTUNE
        train_data = train_data.prefetch(autotune)
        validation_data = validation_data.prefetch(autotune)

        data_augmentation = tf.keras.Sequential(
            [
                tf.keras.layers.RandomFlip("horizontal"),
                tf.keras.layers.RandomRotation(0.12),
                tf.keras.layers.RandomZoom(0.15),
            ]
        )

        base_model = tf.keras.applications.MobileNetV2(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3),
        )
        for layer in base_model.layers[:-30]:
            layer.trainable = False

        inputs = tf.keras.Input(shape=(224, 224, 3))
        x = data_augmentation(inputs)
        x = tf.keras.layers.Rescaling(1.0 / 127.5, offset=-1)(x)
        x = base_model(x, training=False)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dense(256, activation="relu")(x)
        x = tf.keras.layers.Dropout(0.5)(x)
        outputs = tf.keras.layers.Dense(len(class_names), activation="softmax")(x)
        model = tf.keras.Model(inputs=inputs, outputs=outputs)

        model.compile(
            optimizer=tf.keras.optimizers.Adam(0.0001),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        history = model.fit(
            train_data,
            validation_data=validation_data,
            epochs=epochs,
            verbose=1,
        )

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model.save(MODEL_PATH)
        METADATA_PATH.write_text(
            json.dumps(
                {
                    "class_names": class_names,
                    "image_size": [224, 224],
                    "model_family": "Notebook-inspired MobileNetV2 classifier",
                    "selected_classes": [path.name for path in class_directories],
                    "total_images": total_images,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        clear_artifact_cache()

    final_train_accuracy = float(history.history.get("accuracy", [0.0])[-1])
    final_validation_accuracy = float(history.history.get("val_accuracy", [0.0])[-1])

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(MODEL_PATH),
        "class_names": class_names,
        "samples": total_images,
        "epochs": epochs,
        "train_accuracy": final_train_accuracy,
        "validation_accuracy": final_validation_accuracy,
    }
