"""
Trains one classifier per body part on the synthetic demo dataset and
saves a single bundled joblib file at settings.VISION_MODEL_PATH.

Run from the backend/ directory:
    python scripts/train_vision_model.py

This is also what the admin panel's "Train AI Model" action triggers
(via app/tasks/training_tasks.py -> Celery -> this same logic) so the
exact same code path is used whether you train at setup time or retrain
later after the dataset-builder / active-learning pipeline has
accumulated admin-verified images.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.services.vision.features import extract_features
from app.services.vision.synthetic_dataset import LABELS_BY_BODY_PART, generate_dataset


def train_one_body_part(body_part: str, samples_per_label: int = 80) -> Pipeline:
    images, labels = generate_dataset(body_part, samples_per_label=samples_per_label)
    X = np.array([extract_features(img) for img in images])
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200, max_depth=12, random_state=42, class_weight="balanced", n_jobs=-1
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    test_accuracy = pipeline.score(X_test, y_test)
    print(f"  [{body_part}] classes={list(LABELS_BY_BODY_PART[body_part])} test_accuracy={test_accuracy:.3f}")
    return pipeline


def main() -> None:
    print("Training demo vision models (synthetic dataset — see synthetic_dataset.py docstring)...")
    bundle: dict[str, Pipeline] = {}
    for body_part in LABELS_BY_BODY_PART:
        bundle[body_part] = train_one_body_part(body_part)

    out_path = Path(settings.VISION_MODEL_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out_path)
    print(f"Saved bundled model for {len(bundle)} body parts -> {out_path}")


if __name__ == "__main__":
    main()
