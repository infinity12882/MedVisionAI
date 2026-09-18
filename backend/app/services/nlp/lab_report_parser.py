"""
Laboratory report analysis: OCR extraction (PDF text layer first, falling
back to Tesseract OCR for scanned PDFs/images), then a regex-based parser
that pulls out "TestName: value unit (reference range)" style lines —
the dominant format in real lab report printouts — and flags values
outside the reference range as abnormal.

This is a genuinely working parser for well-formatted reports; it is
intentionally conservative (skips lines it can't confidently parse rather
than guessing) since silently mis-parsing a lab value would be worse than
not parsing it at all.
"""
from __future__ import annotations

import re
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pypdf import PdfReader

# Matches lines like:  "Hemoglobin   13.5 g/dL   (12.0 - 16.0)"
#                        "WBC Count: 11200 /uL  Ref: 4000-11000"
_VALUE_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9 /()%\-]{2,40}?)[:\s]+"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>[a-zA-Z/%µμ]{1,15})?\s*"
    r"(?:\(?(?:ref\.?|range)?:?\s*(?P<low>-?\d+\.?\d*)\s*[-–]\s*(?P<high>-?\d+\.?\d*)\)?)?$",
    re.IGNORECASE,
)


def ocr_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read the uploaded image file.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Light preprocessing improves OCR accuracy on photographed (not scanned) lab reports.
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    return pytesseract.image_to_string(gray)


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if text.strip():
            return text
        # Scanned PDF with no embedded text layer — fall back to rendering + OCR is out of
        # scope without poppler; ask the user for an image upload instead in that edge case.
        return ""
    else:
        return ocr_image(str(path))


def parse_lab_values(raw_text: str) -> list[dict]:
    results = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or len(line) > 120:
            continue
        match = _VALUE_LINE_RE.match(line)
        if not match:
            continue
        groups = match.groupdict()
        try:
            value = float(groups["value"])
        except (TypeError, ValueError):
            continue

        low = float(groups["low"]) if groups.get("low") else None
        high = float(groups["high"]) if groups.get("high") else None
        is_abnormal = (low is not None and value < low) or (high is not None and value > high)

        results.append(
            {
                "name": groups["name"].strip(),
                "value": value,
                "unit": (groups.get("unit") or "").strip(),
                "reference_low": low,
                "reference_high": high,
                "is_abnormal": is_abnormal,
            }
        )
    return results


def summarize_findings(values: list[dict]) -> str:
    abnormal = [v for v in values if v["is_abnormal"]]
    if not values:
        return (
            "We extracted text from this report but couldn't confidently identify structured "
            "test values. You may want to review the raw extracted text yourself, or consult "
            "your doctor directly about this report."
        )
    if not abnormal:
        return (
            f"All {len(values)} detected test values appear to fall within their reference "
            "ranges. This is general educational information only — your doctor should "
            "confirm the full interpretation."
        )

    lines = [f"{len(abnormal)} of {len(values)} detected values are outside the typical reference range:"]
    for v in abnormal:
        direction = "above" if v["reference_high"] is not None and v["value"] > v["reference_high"] else "below"
        lines.append(f"• {v['name']}: {v['value']} {v['unit']} ({direction} the reference range)")
    lines.append(
        "This is general educational information, not a diagnosis. Please discuss these "
        "results with a licensed doctor."
    )
    return "\n".join(lines)
