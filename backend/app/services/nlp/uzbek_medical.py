"""
Uzbek-optimized NLP for medical chat: extracts symptoms/diseases from Uzbek text
and improves RAG retrieval by translating to English variants.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple


# Uzbek ↔ English medical terms mapping
UZBEK_MEDICAL_TERMS = {
    # Simptomlar (Symptoms)
    "sariq ko'z": ["jaundice", "yellow eyes"],
    "qizil ko'z": ["red eyes", "eye redness"],
    "og'riq": ["pain", "ache"],
    "bosh og'riq": ["headache", "head pain"],
    "tomok og'riq": ["sore throat", "throat pain"],
    "qon ketish": ["bleeding", "hemorrhage"],
    "isitma": ["fever", "elevated temperature"],
    "shamol": ["cough"],
    "oqayotgan": ["diarrhea", "loose stool"],
    "qusish": ["vomiting", "nausea"],
    "ko'ngil qotishi": ["constipation"],
    "bezovtalik": ["weakness", "fatigue"],
    "charchoq": ["dizzy", "vertigo", "dizziness"],
    "nefas olamay": ["shortness of breath", "dyspnea"],
    "yurak urishi": ["heart palpitations", "palpitations"],
    "teri chiqishi": ["rash", "skin eruption"],
    
    # Kasalliklar (Diseases)
    "gripp": ["flu", "influenza"],
    "covid": ["covid-19", "coronavirus"],
    "odam immunitet yetishmovchiligi": ["hiv", "aids"],
    "shakar kasalligi": ["diabetes"],
    "bosim kasalligi": ["hypertension", "high blood pressure"],
    "ko'ngil kasalligi": ["heart disease", "cardiac disease"],
    "pnevmoniya": ["pneumonia"],
    "bronxit": ["bronchitis"],
    "astma": ["asthma"],
    "angina": ["angina", "tonsillitis"],
    "gastrit": ["gastritis"],
    "openit": ["appendicitis"],
    "urug'ili qorin" : ["colitis", "intestinal inflammation"],
    "o'pka tuberkulezi": ["tuberculosis", "tb"],
    "dermatit": ["dermatitis", "skin inflammation"],
    "allergiyu": ["allergy", "allergic"],
    "migren": ["migraine"],
    "insult": ["stroke"],
    "infarkt": ["heart attack", "myocardial infarction"],
    "sinusit": ["sinusitis"],
    "konungkitivit": ["conjunctivitis"],
    "otit": ["otitis", "ear infection"],
    "pielonefrit": ["pyelonephritis"],
    "sistit": ["cystitis"],
    
    # Etiologiya (Causes)
    "virus": ["viral", "virus"],
    "bakteriya": ["bacterial", "bacteria"],
    "infektsiya": ["infection", "infectious"],
    "stressga bayonnislash": ["stress"],
    "alergy": ["allergy", "allergic"],
    "suitalgan oziq toza emas": ["food poisoning"],
}

# Create reverse mapping (English to Uzbek for completeness)
ENGLISH_TO_UZBEK = {v: k for k, vals in UZBEK_MEDICAL_TERMS.items() for v in vals}


class UzbekMedicalExtractor:
    """Extract medical terms from Uzbek text for better RAG retrieval."""

    def __init__(self):
        self.uzbek_terms = UZBEK_MEDICAL_TERMS
        self.normalized_cache = {}

    def extract_medical_terms(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical terms from Uzbek text.
        Returns: {
            "symptoms": [...],
            "diseases": [...],
            "causes": [...]
        }
        """
        text_lower = text.lower()
        
        found_terms = {
            "symptoms": [],
            "diseases": [],
            "causes": [],
            "all": []
        }
        
        # Simple matching for now (could use fuzzy matching for typos)
        for uzbek_term, english_variants in self.uzbek_terms.items():
            if uzbek_term in text_lower:
                found_terms["all"].extend(english_variants)
                # In production, categorize by source_type from DB
                found_terms["symptoms"].extend(english_variants)
        
        return found_terms

    def expand_query_with_translations(self, original_query: str) -> str:
        """
        Expand query with English translations to improve RAG retrieval.
        Original: "Menga bosh og'riq va isitma bor"
        Result: "Menga bosh og'riq va isitma bor headache fever temperature"
        """
        query = original_query
        
        for uzbek_term, english_variants in self.uzbek_terms.items():
            if uzbek_term in query.lower():
                query += " " + " ".join(english_variants)
        
        return query

    def normalize_text(self, text: str) -> str:
        """
        Normalize Uzbek text (remove diacritics, standardize format).
        """
        # Remove common Uzbek diacritics
        text = text.replace("oʻ", "o'")
        text = text.replace("gʻ", "g'")
        text = text.replace("sʻ", "s'")
        text = text.replace("Oʻ", "O'")
        text = text.replace("Gʻ", "G'")
        text = text.replace("Sʻ", "S'")
        
        return text.strip()


def get_medical_extractor() -> UzbekMedicalExtractor:
    """Get or create Uzbek medical extractor singleton."""
    return UzbekMedicalExtractor()


def translate_term_to_english(uzbek_term: str) -> List[str]:
    """Quick lookup: translate a single Uzbek medical term to English."""
    return UZBEK_MEDICAL_TERMS.get(uzbek_term.lower(), [])


def get_all_english_variants(uzbek_term: str) -> str:
    """Get all English variants of an Uzbek term as a space-separated string."""
    variants = translate_term_to_english(uzbek_term)
    return " ".join(variants) if variants else uzbek_term
