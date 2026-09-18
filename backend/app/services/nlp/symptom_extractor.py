"""
Extracts known Symptom records from free-text input (typed symptoms or a
voice transcript).

This is intentionally a transparent, explainable matcher rather than an
opaque black-box NER model: every match can be traced directly back to the
exact phrase that triggered it, which feeds straight into the Explainable
AI panel on the frontend ("we detected these symptoms in what you wrote").

A small synonym table maps common everyday phrasing ("high temperature",
"runny nose") onto the canonical Symptom names an admin enters into the
knowledge base, without requiring a heavyweight clinical NER model that
would need GPU infrastructure and labeled training data we don't have.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.disease import Symptom

SYNONYMS: dict[str, str] = {
    "high temperature": "fever",
    "temperature": "fever",
    "running nose": "runny nose",
    "stuffy nose": "nasal congestion",
    "blocked nose": "nasal congestion",
    "throwing up": "vomiting",
    "feeling sick": "nausea",
    "tummy ache": "abdominal pain",
    "stomach ache": "abdominal pain",
    "belly pain": "abdominal pain",
    "can't sleep": "insomnia",
    "tired all the time": "fatigue",
    "feeling tired": "fatigue",
    "very tired": "fatigue",
    "exhausted": "fatigue",
    "no energy": "fatigue",
    "short of breath": "shortness of breath",
    "can't breathe": "difficulty breathing",
    "chest tightness": "chest pain",
    "dizzy": "dizziness",
    "itchy skin": "skin itching",
    "red eyes": "eye redness",
    "sore throat": "throat pain",
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_symptoms(db: Session, text: str) -> list[Symptom]:
    normalized = _normalize(text)

    # Expand known synonyms in-place so downstream matching can be pure substring search.
    expanded = normalized
    for phrase, canonical in SYNONYMS.items():
        if phrase in expanded:
            expanded += f" {canonical}"

    all_symptoms = db.query(Symptom).all()
    matched: list[Symptom] = []
    for symptom in all_symptoms:
        symptom_norm = _normalize(symptom.name)
        if symptom_norm and symptom_norm in expanded:
            matched.append(symptom)
            continue
        # Also match if every individual word of a multi-word symptom appears (loose match).
        words = symptom_norm.split()
        if len(words) > 1 and all(w in expanded.split() for w in words):
            matched.append(symptom)

    return matched


def extracted_symptom_names(db: Session, text: str) -> list[str]:
    return [s.name for s in extract_symptoms(db, text)]
