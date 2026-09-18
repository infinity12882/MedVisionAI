"""
AI Nutrition Coach and AI Fitness Coach: generate a personalized plan from
the patient's profile (BMI, activity level, chronic conditions, goals)
using the same Gemini-with-graceful-fallback pattern as the chatbot, so
both features work fully even without a configured GEMINI_API_KEY.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import PatientProfile, User, UserRole
from app.core.config import settings
from app.services.health_score import calculate_health_score

router = APIRouter(prefix="/coach", tags=["AI Coaches"])


class CoachRequest(BaseModel):
    goal: str = Field(description="e.g. 'lose weight', 'build muscle', 'eat healthier', 'improve energy'")


class CoachPlanOut(BaseModel):
    plan: str
    used_fallback: bool


def _profile_context(profile: PatientProfile | None, goal: str) -> str:
    score = calculate_health_score(profile)
    lines = [f"Patient goal: {goal}", f"BMI: {score.bmi} ({score.bmi_category})" if score.bmi else "BMI: unknown"]
    if profile:
        if profile.chronic_conditions:
            lines.append(f"Chronic conditions: {profile.chronic_conditions}")
        if profile.allergies:
            lines.append(f"Allergies: {profile.allergies}")
        if profile.exercise_minutes_per_week is not None:
            lines.append(f"Current exercise: {profile.exercise_minutes_per_week} min/week")
        if profile.sleep_hours_avg is not None:
            lines.append(f"Average sleep: {profile.sleep_hours_avg}h/night")
    lines.append(f"Overall health score: {score.overall_score}/100 ({score.lifestyle_risk} risk)")
    return "\n".join(lines)


def _fallback_nutrition_plan(profile: PatientProfile | None, goal: str) -> str:
    score = calculate_health_score(profile)
    lines = [f"**General Educational Nutrition Plan** (goal: {goal})", ""]
    lines.append("**Sample daily structure:**")
    lines.append("- Breakfast: whole grains + protein + fruit (e.g. oats with berries and yogurt)")
    lines.append("- Lunch: lean protein + vegetables + complex carbs (e.g. grilled chicken, brown rice, salad)")
    lines.append("- Dinner: lighter portion of protein + vegetables (e.g. fish with steamed vegetables)")
    lines.append("- Snacks: nuts, fruit, or vegetables with hummus")
    lines.append("")
    if score.bmi_category == "underweight":
        lines.append("Since your BMI suggests you're underweight, focus on nutrient-dense, calorie-rich foods.")
    elif score.bmi_category in ("overweight", "obese"):
        lines.append("Consider portion control and prioritizing vegetables and lean protein over processed foods.")
    if profile and profile.allergies:
        lines.append(f"⚠️ Remember to avoid foods related to your noted allergies: {profile.allergies}")
    if profile and profile.chronic_conditions:
        lines.append(f"⚠️ Given your noted conditions ({profile.chronic_conditions}), please confirm any dietary plan with your doctor.")
    lines.append("")
    lines.append("This is general educational information, not a personalized clinical nutrition plan. "
                  "Consider consulting a registered dietitian for individualized guidance.")
    return "\n".join(lines)


def _fallback_fitness_plan(profile: PatientProfile | None, goal: str) -> str:
    lines = [f"**General Educational Weekly Workout Plan** (goal: {goal})", ""]
    lines.append("- Monday: 30 min brisk walk or light cardio")
    lines.append("- Tuesday: Bodyweight strength training (squats, push-ups, planks) — 20-30 min")
    lines.append("- Wednesday: Rest or gentle stretching/yoga")
    lines.append("- Thursday: 30 min cardio (cycling, swimming, or brisk walk)")
    lines.append("- Friday: Bodyweight strength training — 20-30 min")
    lines.append("- Saturday: Light active recovery (walk, stretching)")
    lines.append("- Sunday: Rest")
    lines.append("")
    if profile and profile.chronic_conditions:
        lines.append(f"⚠️ Given your noted conditions ({profile.chronic_conditions}), get medical clearance before starting.")
    lines.append("")
    lines.append("This is a general, beginner-safe educational plan, not personalized clinical exercise "
                  "prescription. Adjust intensity based on how your body responds, and consult a doctor "
                  "before starting any new exercise program.")
    return "\n".join(lines)


@router.post("/nutrition", response_model=CoachPlanOut)
def nutrition_plan(
    payload: CoachRequest, db: Session = Depends(get_db), patient: User = Depends(require_role(UserRole.PATIENT))
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    if not settings.GEMINI_API_KEY:
        return CoachPlanOut(plan=_fallback_nutrition_plan(profile, payload.goal), used_fallback=True)

    try:
        from google import genai

        context_text = _profile_context(profile, payload.goal)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=(
                f"Create a general educational nutrition plan with a sample one-day meal structure "
                f"for this patient:\n{context_text}\nKeep it general/educational, note any allergy or "
                "chronic-condition caution, and recommend consulting a registered dietitian for a "
                "personalized plan."
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return CoachPlanOut(plan=_fallback_nutrition_plan(profile, payload.goal), used_fallback=True)
        return CoachPlanOut(plan=text, used_fallback=False)
    except Exception:
        return CoachPlanOut(plan=_fallback_nutrition_plan(profile, payload.goal), used_fallback=True)


@router.post("/fitness", response_model=CoachPlanOut)
def fitness_plan(
    payload: CoachRequest, db: Session = Depends(get_db), patient: User = Depends(require_role(UserRole.PATIENT))
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    if not settings.GEMINI_API_KEY:
        return CoachPlanOut(plan=_fallback_fitness_plan(profile, payload.goal), used_fallback=True)

    try:
        from google import genai

        context_text = _profile_context(profile, payload.goal)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=(
                f"Create a general educational weekly workout plan for this patient:\n{context_text}\n"
                "Keep it beginner-safe and educational, and recommend medical clearance first if any "
                "chronic condition is noted."
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return CoachPlanOut(plan=_fallback_fitness_plan(profile, payload.goal), used_fallback=True)
        return CoachPlanOut(plan=text, used_fallback=False)
    except Exception:
        return CoachPlanOut(plan=_fallback_fitness_plan(profile, payload.goal), used_fallback=True)
