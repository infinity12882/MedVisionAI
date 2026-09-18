export type UserRole = "admin" | "doctor" | "patient";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_email_verified: boolean;
  preferred_language: string;
  dark_mode: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type RiskLevel = "low" | "moderate" | "high" | "emergency";

export interface DiseasePredictionItem {
  disease_id: string | null;
  disease_name: string;
  probability: number;
  explanation: string;
  risk_level: RiskLevel;
  recommended_specialist: string | null;
  medicine_category: string | null;
  home_care_tips: string | null;
  foods_to_eat: string | null;
  foods_to_avoid: string | null;
  recovery_time_days: number | null;
  when_to_visit_hospital: string | null;
  emergency_signs: string | null;
}

export interface ExplainabilityInfo {
  matched_symptoms: string[];
  feature_importance: Record<string, number>;
  confidence_note: string | null;
}

export interface PredictionOut {
  id: string;
  source: "text" | "voice" | "image" | "lab_report";
  input_summary: string;
  results: DiseasePredictionItem[];
  top_disease: string | null;
  top_probability: number | null;
  risk_level: RiskLevel;
  recommended_specialist: string | null;
  recovery_estimate_days: number | null;
  explainability: ExplainabilityInfo;
  created_at: string;
}

export interface ImageDiagnosisOut {
  id: string;
  body_part: string;
  quality_ok: boolean;
  quality_note: string | null;
  predicted_disease: string | null;
  confidence_score: number | null;
  risk_level: string | null;
  explanation: string | null;
  created_at: string;
}

export interface VoiceDiagnosisOut {
  id: string;
  transcript: string | null;
  extracted_symptoms: string[];
  prediction: PredictionOut | null;
  created_at: string;
}

export interface LabReportOut {
  id: string;
  ocr_text: string | null;
  extracted_values: Record<string, unknown>[] | null;
  abnormal_findings: Record<string, unknown>[] | null;
  summary: string | null;
  created_at: string;
}

export interface Symptom {
  id: string;
  name: string;
  description: string | null;
  body_system: string | null;
  created_at: string;
}

export interface DiseaseSymptomOut {
  symptom_id: string;
  importance_score: number;
  symptom: Symptom;
}

export interface Disease {
  id: string;
  name: string;
  alternative_names: string | null;
  icd_code: string | null;
  description: string | null;
  causes: string | null;
  risk_factors: string | null;
  stages: string | null;
  complications: string | null;
  treatment_overview: string | null;
  prevention: string | null;
  nutrition_advice: string | null;
  foods_to_eat: string | null;
  foods_to_avoid: string | null;
  lifestyle_advice: string | null;
  recommended_specialist: string | null;
  emergency_warning_signs: string | null;
  references: string | null;
  tags: string | null;
  severity: string;
  priority: number;
  avg_recovery_days: number | null;
  image_url: string | null;
  video_url: string | null;
  pdf_url: string | null;
  created_at: string;
  symptom_links: DiseaseSymptomOut[];
}

export interface DiseaseListItem {
  id: string;
  name: string;
  severity: string;
  recommended_specialist: string | null;
  tags: string | null;
}

export interface Medication {
  id: string;
  name: string;
  active_ingredient: string | null;
  drug_category: string | null;
  general_indications: string | null;
  contraindications: string | null;
  possible_side_effects: string | null;
  drug_interactions: string | null;
  age_restrictions: string | null;
  pregnancy_considerations: string | null;
  storage_information: string | null;
  educational_notes: string | null;
  prescription_required: boolean;
  linked_disease_tags: string | null;
  created_at: string;
}

export interface RetrievedSource {
  source_type: string;
  source_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrieved_sources: RetrievedSource[];
  used_fallback: boolean;
  created_at: string;
}

export interface ChatConversationOut {
  id: string;
  title: string;
  created_at: string;
}

export interface HealthScoreOut {
  overall_score: number;
  bmi: number | null;
  bmi_category: string | null;
  sleep_score: number;
  stress_score: number;
  water_intake_score: number;
  exercise_score: number;
  lifestyle_risk: "low" | "moderate" | "high";
  recommendations: string[];
}

export interface PatientProfile {
  date_of_birth: string | null;
  sex: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  chronic_conditions: string | null;
  allergies: string | null;
  sleep_hours_avg: number | null;
  water_intake_liters_avg: number | null;
  exercise_minutes_per_week: number | null;
  stress_level: number | null;
}

export interface HistoryItem {
  id: string;
  event_type: string;
  title: string;
  detail: string | null;
  prediction_id: string | null;
  created_at: string;
}

export interface DatasetAnalytics {
  total_diseases: number;
  total_symptoms: number;
  total_medications: number;
  total_articles: number;
  total_images: number;
  total_voice_records: number;
  total_lab_reports: number;
  total_verified_cases: number;
  total_users: number;
  total_doctors: number;
  total_patients: number;
  predictions_last_7_days: { date: string; count: number }[];
  uploads_last_7_days: { date: string; count: number }[];
}

export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}

// ---------- Family ----------
export interface FamilyMember {
  id: string;
  full_name: string;
  relationship: string;
  date_of_birth: string | null;
  sex: string | null;
  chronic_conditions: string | null;
  allergies: string | null;
  notes: string | null;
  created_at: string;
}

// ---------- Care & messaging ----------
export type ConnectionStatus = "pending" | "active" | "ended";

export interface DoctorPublic {
  user_id: string;
  full_name: string;
  specialty: string;
  years_experience: number;
  is_verified: boolean;
}

export interface CareConnectionItem {
  id: string;
  patient_id: string;
  doctor_id: string;
  status: ConnectionStatus;
  created_at: string;
}

export interface DirectConversationItem {
  id: string;
  patient_id: string;
  doctor_id: string;
  other_party_name: string | null;
  last_message: string | null;
  created_at: string;
}

export interface DirectMessageItem {
  id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

// ---------- Appointments ----------
export type AppointmentStatus = "pending" | "confirmed" | "completed" | "cancelled";

export interface TimeSlot {
  id: string;
  doctor_id: string;
  start_time: string;
  end_time: string;
  is_booked: boolean;
}

export interface AppointmentItem {
  id: string;
  patient_id: string;
  doctor_id: string;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
  status: AppointmentStatus;
  doctor_notes: string | null;
  created_at: string;
}

// ---------- Health tracking ----------
export interface PatientMedicationItem {
  id: string;
  medication_name: string;
  dosage: string | null;
  frequency_per_day: number;
  reminder_times: string;
  start_date: string;
  end_date: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SymptomDiaryItem {
  id: string;
  entry_date: string;
  mood_score: number | null;
  energy_level: number | null;
  pain_level: number | null;
  symptoms_text: string | null;
  notes: string | null;
  created_at: string;
}

export interface VaccinationItem {
  id: string;
  vaccine_name: string;
  dose_number: number;
  date_administered: string;
  next_due_date: string | null;
  administered_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface WearableDataPointItem {
  id: string;
  metric_type: string;
  value: number;
  recorded_date: string;
  source: string;
  created_at: string;
}

// ---------- AI Coach ----------
export interface CoachPlan {
  plan: string;
  used_fallback: boolean;
}

// ---------- Emergency ----------
export interface HospitalItem {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string | null;
  specialties: string | null;
  has_emergency_room: boolean;
  distance_km: number | null;
}

export interface PharmacyItem {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string | null;
  is_24h: boolean;
  distance_km: number | null;
}

export interface EmergencyContactItem {
  id: string;
  name: string;
  relationship: string | null;
  phone: string;
  email: string | null;
  created_at: string;
}

// ---------- Platform: API keys / referrals / billing / 2FA ----------
export interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  total_requests: number;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiKeyCreated extends ApiKeyItem {
  full_key: string;
}

export interface ReferralCodeData {
  code: string;
  uses_count: number;
}

export type SubscriptionTier = "free" | "premium";

export interface SubscriptionData {
  tier: SubscriptionTier;
  current_period_end: string | null;
  is_stripe_configured: boolean;
}

export interface TwoFactorSetup {
  secret: string;
  qr_code_data_url: string;
  backup_codes: string[];
}

export interface TrendingCondition {
  disease_name: string;
  case_count: number;
  risk_level: string;
}
