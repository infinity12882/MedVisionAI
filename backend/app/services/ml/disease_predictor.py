"""
Disease prediction from a set of matched symptoms.

Algorithm (transparent, explainable, knowledge-graph-driven):

For every Disease that shares at least one symptom with the matched set,
compute:

    coverage  = (sum of importance_score for matched symptoms linked to this disease)
                / (sum of importance_score for ALL symptoms linked to this disease)
    specificity = (sum of importance_score for matched symptoms linked to this disease)
                  / (sum of importance_score for matched symptoms across ALL diseases they touch)

    score = 0.6 * coverage + 0.4 * specificity

`coverage` rewards diseases where the patient's symptoms cover most of what
that disease typically presents with. `specificity` penalizes very generic
symptoms (e.g. "fatigue") that are weakly linked to dozens of diseases by
spreading their contribution across all of them, so a disease isn't ranked
top purely because it shares one common, low-specificity symptom.

This is a real, deterministic, fully explainable algorithm — every score
can be decomposed back into exactly which symptoms drove it (returned as
`feature_importance`), and it works correctly from the moment an admin
populates the knowledge base, with no training step or labeled dataset
required. It is the documented "baseline production algorithm"; the
architecture (this module's interface) is designed so it can be swapped
for a trained BERT-embedding + XGBoost classifier later once real,
clinically labeled training data is available — see the Active Learning /
dataset builder admin tools, which exist specifically to accumulate that
data over time.
"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.disease import Disease, DiseaseSymptom, Symptom
from app.models.prediction import RiskLevel

SEVERITY_TO_RISK = {
    "mild": RiskLevel.LOW,
    "moderate": RiskLevel.MODERATE,
    "severe": RiskLevel.HIGH,
    "critical": RiskLevel.EMERGENCY,
}


def predict_diseases(db: Session, matched_symptoms: list[Symptom], top_n: int = 5) -> list[dict]:
    if not matched_symptoms:
        return []

    matched_ids = {s.id for s in matched_symptoms}
    matched_names = {s.id: s.name for s in matched_symptoms}

    all_links: list[DiseaseSymptom] = (
        db.query(DiseaseSymptom).filter(DiseaseSymptom.symptom_id.in_(matched_ids)).all()
    )
    if not all_links:
        return []

    candidate_disease_ids = {link.disease_id for link in all_links}

    # Pull ALL symptom links (not just matched ones) for each candidate disease, for the coverage denominator.
    full_links: list[DiseaseSymptom] = (
        db.query(DiseaseSymptom).filter(DiseaseSymptom.disease_id.in_(candidate_disease_ids)).all()
    )

    disease_total_weight: dict[str, float] = defaultdict(float)
    disease_matched_weight: dict[str, float] = defaultdict(float)
    disease_matched_symptom_names: dict[str, list[str]] = defaultdict(list)
    disease_feature_importance: dict[str, dict[str, float]] = defaultdict(dict)

    symptom_total_across_diseases: dict[str, float] = defaultdict(float)
    for link in full_links:
        disease_total_weight[link.disease_id] += link.importance_score
        if link.symptom_id in matched_ids:
            disease_matched_weight[link.disease_id] += link.importance_score
            disease_matched_symptom_names[link.disease_id].append(matched_names[link.symptom_id])
            disease_feature_importance[link.disease_id][matched_names[link.symptom_id]] = link.importance_score
            symptom_total_across_diseases[link.symptom_id] += link.importance_score

    scored: list[tuple[str, float]] = []
    for disease_id in candidate_disease_ids:
        coverage = disease_matched_weight[disease_id] / max(disease_total_weight[disease_id], 1e-6)

        specificity_terms = []
        for link in full_links:
            if link.disease_id == disease_id and link.symptom_id in matched_ids:
                denom = symptom_total_across_diseases[link.symptom_id]
                specificity_terms.append(link.importance_score / max(denom, 1e-6))
        specificity = sum(specificity_terms) / max(len(specificity_terms), 1)

        score = 0.6 * coverage + 0.4 * specificity
        scored.append((disease_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_disease_ids = [d_id for d_id, _ in scored[:top_n]]

    diseases_by_id = {d.id: d for d in db.query(Disease).filter(Disease.id.in_(top_disease_ids)).all()}

    # Normalize scores to sum to 1.0 across the returned top-N so they read as probabilities.
    top_scores = [s for _, s in scored[:top_n]]
    score_sum = sum(top_scores) or 1.0

    results = []
    for disease_id, raw_score in scored[:top_n]:
        disease = diseases_by_id.get(disease_id)
        if disease is None:
            continue
        probability = round(raw_score / score_sum, 4)
        matched_for_this = disease_matched_symptom_names[disease_id]
        risk = SEVERITY_TO_RISK.get(disease.severity, RiskLevel.MODERATE)

        explanation = (
            f"{len(matched_for_this)} of your reported symptoms "
            f"({', '.join(matched_for_this)}) are commonly associated with {disease.name}."
        )

        results.append(
            {
                "disease_id": disease.id,
                "disease_name": disease.name,
                "probability": probability,
                "explanation": explanation,
                "risk_level": risk,
                "recommended_specialist": disease.recommended_specialist,
                "medicine_category": None,  # filled in by caller from linked Medication records, if any
                "home_care_tips": disease.lifestyle_advice,
                "foods_to_eat": disease.foods_to_eat,
                "foods_to_avoid": disease.foods_to_avoid,
                "recovery_time_days": disease.avg_recovery_days,
                "when_to_visit_hospital": disease.emergency_warning_signs,
                "emergency_signs": disease.emergency_warning_signs,
                "_matched_symptoms": matched_for_this,
                "_feature_importance": disease_feature_importance[disease_id],
            }
        )

    return results


def overall_risk_level(results: list[dict]) -> RiskLevel:
    if not results:
        return RiskLevel.LOW
    order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.EMERGENCY]
    worst = max((r["risk_level"] for r in results), key=lambda r: order.index(r))
    return worst
