"""
Synthetic demo-dataset generator for the vision classification pipeline.

IMPORTANT — read before deploying to real patients:
This module procedurally generates synthetic images with controlled color
and texture properties (redness level, patchiness, spot density) to stand
in for real clinical photos, which are not available in this build
environment (they require licensed, IRB-approved, clinically-labeled
datasets such as ISIC for skin lesions). The classifier trained on this
data demonstrates a fully working end-to-end pipeline — image upload ->
quality gate -> feature extraction -> classification -> explanation -> a
specialist recommendation pulled from the knowledge base — but its
predictions are NOT clinically meaningful and must not be used for real
diagnosis. Swap in a real labeled dataset (the admin panel's "Image
Dataset Builder" exists specifically to accumulate doctor-verified images
over time) and retrain via `scripts/train_vision_model.py` before any
real-world use.
"""
from __future__ import annotations

import numpy as np

LABELS_BY_BODY_PART: dict[str, list[str]] = {
    "skin": ["Healthy Skin", "Eczema", "Fungal Skin Infection", "Acne", "Psoriasis"],
    "eye": ["Healthy Eye", "Conjunctivitis", "Stye"],
    "tongue": ["Healthy Tongue", "Oral Thrush", "Geographic Tongue"],
    "nails": ["Healthy Nails", "Fungal Nail Infection", "Nail Psoriasis"],
    "throat": ["Healthy Throat", "Strep Throat", "Tonsillitis"],
    "wound": ["Healing Wound", "Infected Wound", "Fresh Wound"],
}

# (base_bgr_color, redness_boost, patchiness, spot_density) per label — hand-tuned so
# classes are visually separable for demo purposes.
_LABEL_PROFILES: dict[str, dict] = {
    "Healthy Skin": dict(base=(150, 180, 210), redness=0.0, patchiness=0.05, spots=0.0),
    "Eczema": dict(base=(110, 130, 200), redness=0.45, patchiness=0.55, spots=0.1),
    "Fungal Skin Infection": dict(base=(120, 150, 180), redness=0.2, patchiness=0.4, spots=0.5),
    "Acne": dict(base=(140, 160, 205), redness=0.35, patchiness=0.15, spots=0.7),
    "Psoriasis": dict(base=(180, 190, 215), redness=0.3, patchiness=0.6, spots=0.2),
    "Healthy Eye": dict(base=(200, 220, 230), redness=0.02, patchiness=0.05, spots=0.0),
    "Conjunctivitis": dict(base=(150, 170, 220), redness=0.6, patchiness=0.2, spots=0.0),
    "Stye": dict(base=(160, 175, 215), redness=0.4, patchiness=0.1, spots=0.3),
    "Healthy Tongue": dict(base=(150, 130, 210), redness=0.1, patchiness=0.05, spots=0.0),
    "Oral Thrush": dict(base=(220, 220, 230), redness=0.05, patchiness=0.5, spots=0.3),
    "Geographic Tongue": dict(base=(160, 140, 205), redness=0.15, patchiness=0.6, spots=0.1),
    "Healthy Nails": dict(base=(200, 200, 210), redness=0.0, patchiness=0.05, spots=0.0),
    "Fungal Nail Infection": dict(base=(170, 190, 160), redness=0.05, patchiness=0.45, spots=0.2),
    "Nail Psoriasis": dict(base=(190, 180, 190), redness=0.2, patchiness=0.5, spots=0.4),
    "Healthy Throat": dict(base=(170, 140, 210), redness=0.1, patchiness=0.05, spots=0.0),
    "Strep Throat": dict(base=(140, 120, 220), redness=0.55, patchiness=0.2, spots=0.6),
    "Tonsillitis": dict(base=(150, 130, 215), redness=0.45, patchiness=0.3, spots=0.4),
    "Healing Wound": dict(base=(160, 170, 200), redness=0.25, patchiness=0.3, spots=0.0),
    "Infected Wound": dict(base=(120, 150, 190), redness=0.5, patchiness=0.5, spots=0.4),
    "Fresh Wound": dict(base=(100, 110, 220), redness=0.65, patchiness=0.2, spots=0.0),
}


def _generate_image(profile: dict, size: int, rng: np.random.Generator) -> np.ndarray:
    base = np.array(profile["base"], dtype="float32")
    img = np.tile(base, (size, size, 1))

    # Redness boost: push toward red channel (BGR, so index 2).
    img[:, :, 2] += profile["redness"] * 60 * rng.random()

    # Patchiness: low-frequency blotches via blurred noise.
    blotch = rng.normal(0, 1, size=(size // 8, size // 8, 1)).astype("float32")
    blotch = np.repeat(np.repeat(blotch, 8, axis=0), 8, axis=1)[:size, :size, :]
    img += blotch * profile["patchiness"] * 35

    # Spots: random small dark/red dots.
    n_spots = int(profile["spots"] * 40)
    for _ in range(n_spots):
        cx, cy = rng.integers(0, size, size=2)
        r = rng.integers(2, 6)
        yy, xx = np.ogrid[:size, :size]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        img[mask, 2] += 30
        img[mask, 0] -= 15

    # General sensor noise so the classifier doesn't overfit to perfectly flat synthetic regions.
    img += rng.normal(0, 6, size=img.shape)

    return np.clip(img, 0, 255).astype("uint8")


def generate_dataset(
    body_part: str, samples_per_label: int = 60, image_size: int = 256, seed: int = 42
) -> tuple[list[np.ndarray], list[str]]:
    labels = LABELS_BY_BODY_PART[body_part]
    rng = np.random.default_rng(seed)

    images: list[np.ndarray] = []
    image_labels: list[str] = []
    for label in labels:
        profile = _LABEL_PROFILES[label]
        for _ in range(samples_per_label):
            images.append(_generate_image(profile, image_size, rng))
            image_labels.append(label)

    return images, image_labels
