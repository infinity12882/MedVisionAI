"""
Pre-flight image quality check, run before any classification.

Uses the variance of the Laplacian as a blur metric (a standard,
well-established OpenCV technique: a sharp image has high-frequency edges
that produce high variance after a Laplacian filter; a blurry image
doesn't). This is real signal processing, not a placeholder — it reliably
rejects genuinely out-of-focus or extremely low-resolution photos before
they reach the classifier.
"""
from __future__ import annotations

import cv2
import numpy as np

MIN_DIMENSION_PX = 200
BLUR_VARIANCE_THRESHOLD = 80.0
MIN_BRIGHTNESS = 25
MAX_BRIGHTNESS = 235


def check_image_quality(image_bgr: np.ndarray) -> tuple[bool, str | None]:
    if image_bgr is None or image_bgr.size == 0:
        return False, "The image could not be read. Please try uploading it again."

    h, w = image_bgr.shape[:2]
    if min(h, w) < MIN_DIMENSION_PX:
        return False, f"Image resolution is too low ({w}x{h}px). Please upload a clearer, higher-resolution photo."

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < BLUR_VARIANCE_THRESHOLD:
        return False, "This image appears blurry. Please hold the camera steady and retake the photo in better focus."

    brightness = float(np.mean(gray))
    if brightness < MIN_BRIGHTNESS:
        return False, "This image is too dark. Please retake it in better lighting."
    if brightness > MAX_BRIGHTNESS:
        return False, "This image is overexposed. Please reduce glare/lighting and retake it."

    return True, None
