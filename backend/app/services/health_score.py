"""
AI Health Score: combines a patient's self-reported lifestyle metrics into
a single 0-100 score plus sub-scores, using standard public-health
reference ranges (WHO BMI categories, CDC sleep/exercise/hydration
guidelines). This is straightforward, well-established scoring logic —
not a black box — so every number on the dashboard can be explained.
"""
from __future__ import annotations

from app.models.user import PatientProfile
from app.schemas.misc import HealthScoreOut


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


def _bmi_score(bmi: float | None) -> float:
    if bmi is None:
        return 70.0  # neutral default when data is missing
    if 18.5 <= bmi < 25:
        return 100.0
    if 17 <= bmi < 18.5 or 25 <= bmi < 30:
        return 70.0
    if 16 <= bmi < 17 or 30 <= bmi < 35:
        return 45.0
    return 20.0


def _sleep_score(hours: float | None) -> float:
    if hours is None:
        return 70.0
    if 7 <= hours <= 9:
        return 100.0
    if 6 <= hours < 7 or 9 < hours <= 10:
        return 75.0
    if 5 <= hours < 6:
        return 50.0
    return 25.0


def _stress_score(level: int | None) -> float:
    if level is None:
        return 70.0
    # level is 1 (very low stress) to 10 (extreme stress) — invert so higher score = better.
    return max(0.0, 100.0 - (level - 1) * (100.0 / 9))


def _water_score(liters: float | None) -> float:
    if liters is None:
        return 70.0
    if liters >= 2.0:
        return 100.0
    if liters >= 1.5:
        return 75.0
    if liters >= 1.0:
        return 50.0
    return 25.0


def _exercise_score(minutes_per_week: int | None) -> float:
    if minutes_per_week is None:
        return 70.0
    if minutes_per_week >= 150:  # WHO recommended minimum
        return 100.0
    if minutes_per_week >= 75:
        return 70.0
    if minutes_per_week >= 30:
        return 45.0
    return 20.0


def calculate_health_score(profile: PatientProfile | None) -> HealthScoreOut:
    bmi = None
    bmi_category = None
    if profile and profile.height_cm and profile.weight_kg and profile.height_cm > 0:
        height_m = profile.height_cm / 100
        bmi = round(profile.weight_kg / (height_m**2), 1)
        bmi_category = _bmi_category(bmi)

    bmi_s = _bmi_score(bmi)
    sleep_s = _sleep_score(profile.sleep_hours_avg if profile else None)
    stress_s = _stress_score(profile.stress_level if profile else None)
    water_s = _water_score(profile.water_intake_liters_avg if profile else None)
    exercise_s = _exercise_score(profile.exercise_minutes_per_week if profile else None)

    overall = round((bmi_s * 0.25 + sleep_s * 0.2 + stress_s * 0.2 + water_s * 0.15 + exercise_s * 0.2), 1)

    if overall >= 80:
        lifestyle_risk = "low"
    elif overall >= 55:
        lifestyle_risk = "moderate"
    else:
        lifestyle_risk = "high"

    recommendations = []
    if bmi_s < 70:
        recommendations.append("Consider speaking with a doctor or nutritionist about reaching a healthier BMI range.")
    if sleep_s < 70:
        recommendations.append("Aim for 7-9 hours of sleep per night for better recovery and concentration.")
    if stress_s < 70:
        recommendations.append("Try stress-reduction techniques like breathing exercises, walks, or talking to someone you trust.")
    if water_s < 70:
        recommendations.append("Try to drink at least 2 liters of water a day, more if you're physically active.")
    if exercise_s < 70:
        recommendations.append("Aim for at least 150 minutes of moderate exercise per week, like brisk walking.")
    if not recommendations:
        recommendations.append("Great job! Keep maintaining your current healthy habits.")

    return HealthScoreOut(
        overall_score=overall,
        bmi=bmi,
        bmi_category=bmi_category,
        sleep_score=sleep_s,
        stress_score=stress_s,
        water_intake_score=water_s,
        exercise_score=exercise_s,
        lifestyle_risk=lifestyle_risk,
        recommendations=recommendations,
    )
