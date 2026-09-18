"""
Vision classifier wrapper. Loads a bundle of {body_part: trained sklearn
Pipeline} produced by `scripts/train_vision_model.py` and exposes a single
`predict(body_part, image_bgr)` call used by the image-diagnosis endpoint.

See `synthetic_dataset.py` for an important disclosure about training data.
"""
from __future__ import annotations

import threading
from pathlib import Path

import joblib
import numpy as np

from app.core.config import settings
from app.services.vision.features import extract_features

_lock = threading.Lock()
_model_bundle: dict | None = None


def _load_bundle() -> dict:
    global _model_bundle
    with _lock:
        if _model_bundle is None:
            path = Path(settings.VISION_MODEL_PATH)
            if not path.exists():
                raise FileNotFoundError(
                    f"No trained vision model found at {path}. Run "
                    "`python scripts/train_vision_model.py` first."
                )
            _model_bundle = joblib.load(path)
        return _model_bundle


def is_model_available() -> bool:
    return Path(settings.VISION_MODEL_PATH).exists()


def predict(body_part: str, image_bgr: np.ndarray) -> dict:
    """
    Returns: {predicted_label, confidence, class_probabilities: {label: prob}}
    """
    bundle = _load_bundle()
    if body_part not in bundle:
        raise ValueError(f"No trained model for body part '{body_part}'")

    pipeline = bundle[body_part]
    features = extract_features(image_bgr).reshape(1, -1)

    probabilities = pipeline.predict_proba(features)[0]
    classes = pipeline.classes_
    top_idx = int(np.argmax(probabilities))

    class_probabilities = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}

    return {
        "predicted_label": classes[top_idx],
        "confidence": round(float(probabilities[top_idx]), 4),
        "class_probabilities": class_probabilities,
    }
