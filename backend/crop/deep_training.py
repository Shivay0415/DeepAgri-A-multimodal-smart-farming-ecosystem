from __future__ import annotations

"""
Notebook-derived deep-learning utilities for Module 1.

These helpers are adapted from the user's `capstone (1) (1).py` and
`capstone (2).ipynb` files so the crop module can optionally train a
deeper PyTorch MLP or a TabTransformer-style model.
"""

import random
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


SEED = 42


def _load_torch():
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as exc:
        raise ValueError(
            "Notebook-style crop trainers require PyTorch. Install torch locally to use "
            "'notebook-mlp' or 'notebook-transformer'."
        ) from exc

    return torch, nn, DataLoader, TensorDataset


def _set_seed(torch_module) -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch_module.manual_seed(SEED)


def _build_mlp(
    nn,
    in_dim: int,
    num_classes: int,
    width: int = 256,
    depth: int = 4,
    dropout: float = 0.2,
):
    layers = []
    current_dim = in_dim
    for _ in range(depth):
        layers.extend(
            [
                nn.Linear(current_dim, width),
                nn.ReLU(),
                nn.LayerNorm(width),
                nn.Dropout(dropout),
            ]
        )
        current_dim = width
    layers.append(nn.Linear(current_dim, num_classes))
    return nn.Sequential(*layers)


def _build_tab_transformer(
    torch_module,
    nn,
    *,
    num_features: int,
    num_classes: int,
    bins_per_feature: int = 12,
    d_model: int = 64,
    nhead: int = 4,
    nlayers: int = 3,
    dim_feedforward: int = 128,
    dropout: float = 0.1,
):
    class TabTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.num_features = num_features
            self.bins_per_feature = bins_per_feature
            self.embeddings = nn.ModuleList(
                [nn.Embedding(bins_per_feature, d_model) for _ in range(num_features)]
            )
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                batch_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=nlayers)
            self.classifier = nn.Sequential(nn.LayerNorm(d_model), nn.Linear(d_model, num_classes))
            self.register_buffer("bin_edges", torch_module.zeros(num_features, bins_per_feature - 1))

        def fit_bins(self, features: np.ndarray) -> None:
            edges = []
            for index in range(self.num_features):
                quantiles = np.quantile(
                    features[:, index],
                    np.linspace(0, 1, self.bins_per_feature + 1)[1:-1],
                )
                edges.append(quantiles.astype("float32"))
            self.bin_edges = torch_module.tensor(np.stack(edges), dtype=torch_module.float32)

        def _digitize(self, feature_tensor):
            _, feature_count = feature_tensor.shape
            ids = torch_module.zeros_like(
                feature_tensor,
                dtype=torch_module.long,
                device=feature_tensor.device,
            )
            for index in range(feature_count):
                ids[:, index] = torch_module.bucketize(
                    feature_tensor[:, index],
                    self.bin_edges[index].to(feature_tensor.device),
                )
            return ids

        def forward(self, feature_tensor):
            token_ids = self._digitize(feature_tensor)
            embedded_tokens = []
            for index in range(self.num_features):
                embedded_tokens.append(self.embeddings[index](token_ids[:, index]))
            tokens = torch_module.stack(embedded_tokens, dim=1)
            encoded = self.encoder(tokens)
            pooled = encoded.mean(dim=1)
            return self.classifier(pooled)

    return TabTransformer()


def train_notebook_model(
    *,
    rows: list[dict],
    feature_order: list[str],
    architecture: str,
    epochs: int = 80,
    learning_rate: float = 1e-3,
) -> tuple[dict[str, Any], dict[str, Any]]:
    torch_module, nn, DataLoader, TensorDataset = _load_torch()
    _set_seed(torch_module)

    feature_matrix = np.array(
        [[row[feature_name] for feature_name in feature_order] for row in rows],
        dtype="float32",
    )
    labels = [row["label"] for row in rows]

    encoded_labels = LabelEncoder().fit_transform(labels)

    class_counts = np.bincount(encoded_labels)
    valid_classes = {index for index, count in enumerate(class_counts) if count >= 2}
    filtered_indices = [index for index, value in enumerate(encoded_labels) if value in valid_classes]
    if len(filtered_indices) < 10:
        raise ValueError("Notebook-style training needs at least 10 rows after class filtering.")

    X_filtered = feature_matrix[filtered_indices]
    filtered_labels = [labels[index] for index in filtered_indices]
    label_encoder = LabelEncoder()
    y_filtered = label_encoder.fit_transform(filtered_labels)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X_filtered,
        y_filtered,
        test_size=0.3,
        random_state=SEED,
        stratify=y_filtered,
    )
    X_val, _, y_val, _ = train_test_split(
        X_temp,
        y_temp,
        test_size=0.5,
        random_state=SEED,
        stratify=y_temp,
    )

    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train).astype("float32")
    X_val_scaled = scaler.transform(X_val).astype("float32")

    train_loader = DataLoader(
        TensorDataset(
            torch_module.tensor(X_train_scaled),
            torch_module.tensor(y_train, dtype=torch_module.long),
        ),
        batch_size=128,
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(
            torch_module.tensor(X_val_scaled),
            torch_module.tensor(y_val, dtype=torch_module.long),
        ),
        batch_size=256,
        shuffle=False,
    )

    num_classes = len({rows[index]["label"] for index in filtered_indices})
    if architecture == "notebook-transformer":
        model = _build_tab_transformer(
            torch_module,
            nn,
            num_features=len(feature_order),
            num_classes=num_classes,
        )
        model.fit_bins(X_train_scaled)
        config = {
            "bins_per_feature": model.bins_per_feature,
            "d_model": 64,
            "nhead": 4,
            "nlayers": 3,
            "dim_feedforward": 128,
            "dropout": 0.1,
        }
        model_family = "Notebook-derived TabTransformer-style crop classifier"
    else:
        model = _build_mlp(nn, len(feature_order), num_classes)
        config = {"width": 256, "depth": 4, "dropout": 0.2}
        model_family = "Notebook-derived PyTorch MLP crop classifier"

    optimizer = torch_module.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    best_val_accuracy = -1.0
    best_state = None

    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            logits = model(xb)
            loss = criterion(logits, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch_module.no_grad():
            for xb, yb in val_loader:
                predictions = model(xb).argmax(dim=1)
                correct += (predictions == yb).sum().item()
                total += yb.size(0)

        val_accuracy = correct / max(total, 1)
        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            best_state = {key: value.cpu() for key, value in model.state_dict().items()}

    if best_state is None:
        raise ValueError("Notebook-style crop training did not produce a valid model state.")

    artifact = {
        "artifact_type": "torch",
        "architecture": architecture,
        "state_dict": best_state,
        "labels": list(label_encoder.classes_),
        "feature_order": feature_order,
        "feature_defaults": {
            feature_name: round(sum(row[feature_name] for row in rows) / len(rows), 4)
            for feature_name in feature_order
        },
        "model_family": model_family,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "config": config,
        "validation_accuracy": round(float(best_val_accuracy), 4),
    }
    if architecture == "notebook-transformer":
        artifact["bin_edges"] = model.bin_edges.cpu()

    summary = {
        "samples": len(rows),
        "classes": sorted(set(labels)),
        "validation_accuracy": round(float(best_val_accuracy), 4),
        "trainer": architecture,
    }
    return artifact, summary


def predict_torch_probabilities(raw_artifact: dict[str, Any], feature_values: list[float]) -> list[tuple[str, float]]:
    torch_module, nn, _, _ = _load_torch()

    labels = list(raw_artifact["labels"])
    architecture = raw_artifact["architecture"]
    if architecture == "notebook-transformer":
        model = _build_tab_transformer(
            torch_module,
            nn,
            num_features=len(raw_artifact["feature_order"]),
            num_classes=len(labels),
            **raw_artifact["config"],
        )
        model.bin_edges = raw_artifact["bin_edges"]
    else:
        model = _build_mlp(
            nn,
            len(raw_artifact["feature_order"]),
            len(labels),
            **raw_artifact["config"],
        )

    model.load_state_dict(raw_artifact["state_dict"])
    model.eval()

    means = np.array(raw_artifact["scaler_mean"], dtype="float32")
    scales = np.array(raw_artifact["scaler_scale"], dtype="float32")
    scales = np.where(scales == 0, 1.0, scales)
    standardized = (np.array(feature_values, dtype="float32") - means) / scales

    with torch_module.no_grad():
        logits = model(torch_module.tensor([standardized], dtype=torch_module.float32))
        probabilities = torch_module.softmax(logits, dim=1)[0].tolist()

    return sorted(zip(labels, probabilities), key=lambda item: item[1], reverse=True)
