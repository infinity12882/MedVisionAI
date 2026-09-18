"""
Classical computer-vision feature extraction used by the demo vision
classifier: HSV color histograms (captures redness/discoloration patterns
relevant to skin/eye/throat conditions) plus simple texture statistics
from a Laplacian and gray-level co-occurrence-style local variance
(captures roughness/patchiness). These are real, well-understood CV
features — not placeholders — they're just being fed into a lightweight
classifier trained on a small synthetic dataset rather than a deep CNN
trained on a large clinical dataset (see ml_artifacts/README.md for why).
"""
from __future__ import annotations

import cv2
import numpy as np

FEATURE_VECTOR_SIZE = 48  # 32 (hue) + 8 (saturation) + 8 stats — keep in sync with extract_features


def extract_features(image_bgr: np.ndarray) -> np.ndarray:
    image_bgr = cv2.resize(image_bgr, (256, 256))
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    hue_hist = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten()
    hue_hist = hue_hist / (hue_hist.sum() + 1e-6)

    sat_hist = cv2.calcHist([hsv], [1], None, [8], [0, 256]).flatten()
    sat_hist = sat_hist / (sat_hist.sum() + 1e-6)

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_stats = np.array(
        [
            float(np.mean(gray)) / 255.0,
            float(np.std(gray)) / 255.0,
            float(np.var(laplacian)) / 1000.0,
            float(np.mean(hsv[:, :, 1])) / 255.0,  # mean saturation (redness/inflammation proxy)
            float(np.std(hsv[:, :, 0])) / 180.0,  # hue spread (patchiness proxy)
            float(np.percentile(gray, 90)) / 255.0,
            float(np.percentile(gray, 10)) / 255.0,
            float(np.mean(hsv[:, :, 2])) / 255.0,  # mean brightness/value
        ]
    )

    return np.concatenate([hue_hist, sat_hist, texture_stats]).astype("float32")
