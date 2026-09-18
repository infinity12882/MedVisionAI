import { apiClient } from "./client";
import type {
  AppointmentItem,
  AppointmentStatus,
  ApiKeyCreated,
  ApiKeyItem,
  CareConnectionItem,
  ChatConversationOut,
  ChatMessageOut,
  CoachPlan,
  DatasetAnalytics,
  Disease,
  DiseaseListItem,
  DirectConversationItem,
  DirectMessageItem,
  DoctorPublic,
  EmergencyContactItem,
  FamilyMember,
  HealthScoreOut,
  HistoryItem,
  HospitalItem,
  ImageDiagnosisOut,
  LabReportOut,
  Medication,
  PatientMedicationItem,
  PatientProfile,
  PharmacyItem,
  PredictionOut,
  ReferralCodeData,
  SubscriptionData,
  Symptom,
  SymptomDiaryItem,
  TimeSlot,
  TokenPair,
  TrendingCondition,
  TwoFactorSetup,
  User,
  UserRole,
  VaccinationItem,
  VoiceDiagnosisOut,
  WearableDataPointItem,
} from "@/types";

export async function downloadBlob(url: string) {
  const response = await apiClient.get(url, { responseType: 'blob' });
  const objectUrl = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = objectUrl;
  const contentDisposition = response.headers['content-disposition'];
  let filename = 'download';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) filename = match[1];
  }
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectUrl);
}

// ---------- Auth ----------
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: UserRole; referral_code?: string }) =>
    apiClient.post<User>("/auth/register", data).then((r) => r.data),
  login: (data: { email: string; password: string; totp_code?: string }) =>
    apiClient.post<TokenPair>("/auth/login", data).then((r) => r.data),
  me: () => apiClient.get<User>("/auth/me").then((r) => r.data),
  requestPasswordReset: (email: string) => apiClient.post("/auth/password-reset/request", { email }),
};

// ---------- Users ----------
export const usersApi = {
  updateMe: (data: Partial<Pick<User, "full_name" | "preferred_language" | "dark_mode">>) =>
    apiClient.put<User>("/users/me", data).then((r) => r.data),
  getPatientProfile: () => apiClient.get<PatientProfile>("/users/me/patient-profile").then((r) => r.data),
  updatePatientProfile: (data: Partial<PatientProfile>) =>
    apiClient.put<PatientProfile>("/users/me/patient-profile", data).then((r) => r.data),
  getHealthScore: () => apiClient.get<HealthScoreOut>("/users/me/health-score").then((r) => r.data),
};

// ---------- Knowledge base ----------
export const diseasesApi = {
  list: (search?: string) =>
    apiClient.get<DiseaseListItem[]>("/diseases", { params: { search } }).then((r) => r.data),
  get: (id: string) => apiClient.get<Disease>(`/diseases/${id}`).then((r) => r.data),
  create: (data: Partial<Disease> & { name: string; symptoms?: { symptom_id: string; importance_score: number }[] }) =>
    apiClient.post<Disease>("/diseases", data).then((r) => r.data),
  update: (id: string, data: Partial<Disease> & { symptoms?: { symptom_id: string; importance_score: number }[] }) => apiClient.put<Disease>(`/diseases/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/diseases/${id}`),
};

export const symptomsApi = {
  list: (search?: string) => apiClient.get<Symptom[]>("/symptoms", { params: { search } }).then((r) => r.data),
  create: (data: { name: string; description?: string; body_system?: string }) =>
    apiClient.post<Symptom>("/symptoms", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/symptoms/${id}`),
};

export const medicationsApi = {
  list: (search?: string) => apiClient.get<Medication[]>("/medications", { params: { search } }).then((r) => r.data),
  create: (data: Partial<Medication> & { name: string }) =>
    apiClient.post<Medication>("/medications", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/medications/${id}`),
};

// ---------- Diagnosis ----------
export const diagnosisApi = {
  checkSymptoms: (symptoms_text: string, family_member_id?: string) =>
    apiClient.post<PredictionOut>("/diagnosis/text", { symptoms_text, family_member_id }).then((r) => r.data),

  diagnoseImage: (file: File, bodyPart: string, seriesId?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("body_part", bodyPart);
    if (seriesId) form.append("series_id", seriesId);
    return apiClient
      .post<ImageDiagnosisOut>("/diagnosis/image", form, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },

  diagnoseVoice: (file: File | Blob, filename = "recording.webm") => {
    const form = new FormData();
    form.append("file", file, filename);
    return apiClient
      .post<VoiceDiagnosisOut>("/diagnosis/voice", form, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },

  analyzeLabReport: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient
      .post<LabReportOut>("/diagnosis/lab-report", form, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
};

// ---------- Chat ----------
export const chatApi = {
  listConversations: () => apiClient.get<ChatConversationOut[]>("/chat/conversations").then((r) => r.data),
  listMessages: (conversationId: string) =>
    apiClient.get<ChatMessageOut[]>(`/chat/conversations/${conversationId}/messages`).then((r) => r.data),
  send: (message: string, conversationId?: string) =>
    apiClient
      .post<{ conversation_id: string; user_message: ChatMessageOut; assistant_message: ChatMessageOut }>(
        "/chat/send",
        { message, conversation_id: conversationId }
      )
      .then((r) => r.data),
};

// ---------- History / reports ----------
export const historyApi = {
  list: () => apiClient.get<HistoryItem[]>("/history").then((r) => r.data),
  downloadPdf: (predictionId: string) => downloadBlob(`/reports/${predictionId}/pdf`),
};

// ---------- Admin ----------
export const adminApi = {
  analytics: () => apiClient.get<DatasetAnalytics>("/admin/analytics").then((r) => r.data),
  trendingConditions: () => apiClient.get<TrendingCondition[]>("/admin/analytics/trending-conditions").then((r) => r.data),
  listUsers: (role?: UserRole) => apiClient.get<User[]>("/admin/users", { params: { role } }).then((r) => r.data),
  changeUserRole: (userId: string, newRole: UserRole) =>
    apiClient.put<User>(`/admin/users/${userId}/role`, null, { params: { new_role: newRole } }).then((r) => r.data),
  deactivateUser: (userId: string) => apiClient.put<User>(`/admin/users/${userId}/deactivate`).then((r) => r.data),
  activateUser: (userId: string) => apiClient.put<User>(`/admin/users/${userId}/activate`).then((r) => r.data),
  auditLogs: (limit = 100) => apiClient.get(`/admin/audit-logs`, { params: { limit } }).then((r) => r.data),
  reindexKnowledgeBase: () => apiClient.post("/admin/knowledge-base/reindex").then((r) => r.data),
  retrainVisionModel: () => apiClient.post("/admin/models/retrain-vision").then((r) => r.data),
};

// ---------- Family ----------
export const familyApi = {
  list: () => apiClient.get<FamilyMember[]>("/family").then((r) => r.data),
  create: (data: Omit<FamilyMember, "id" | "created_at">) =>
    apiClient.post<FamilyMember>("/family", data).then((r) => r.data),
  update: (id: string, data: Omit<FamilyMember, "id" | "created_at">) =>
    apiClient.put<FamilyMember>(`/family/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/family/${id}`),
};

// ---------- Care & messaging ----------
export const careApi = {
  listDoctors: () => apiClient.get<DoctorPublic[]>("/doctors").then((r) => r.data),
  requestConnection: (doctorId: string) =>
    apiClient.post<CareConnectionItem>(`/care-connections/${doctorId}`).then((r) => r.data),
  myConnections: () => apiClient.get<CareConnectionItem[]>("/care-connections/my").then((r) => r.data),
  acceptConnection: (connectionId: string) =>
    apiClient.put<CareConnectionItem>(`/care-connections/${connectionId}/accept`).then((r) => r.data),
  listConversations: () => apiClient.get<DirectConversationItem[]>("/messages/conversations").then((r) => r.data),
  getMessages: (conversationId: string) =>
    apiClient.get<DirectMessageItem[]>(`/messages/conversations/${conversationId}`).then((r) => r.data),
  sendMessage: (otherUserId: string, content: string) =>
    apiClient.post<DirectMessageItem>(`/messages/with/${otherUserId}`, { content }).then((r) => r.data),
};

// ---------- Appointments ----------
export const appointmentsApi = {
  createSlot: (startTime: string, endTime: string) =>
    apiClient.post<TimeSlot>("/appointments/slots", { start_time: startTime, end_time: endTime }).then((r) => r.data),
  listSlots: (doctorId: string) => apiClient.get<TimeSlot[]>(`/appointments/slots/${doctorId}`).then((r) => r.data),
  deleteSlot: (slotId: string) => apiClient.delete(`/appointments/slots/${slotId}`),
  book: (doctorId: string, slotId: string, reason?: string) =>
    apiClient.post<AppointmentItem>("/appointments", { doctor_id: doctorId, slot_id: slotId, reason }).then((r) => r.data),
  myAppointments: () => apiClient.get<AppointmentItem[]>("/appointments/my").then((r) => r.data),
  updateStatus: (appointmentId: string, status: AppointmentStatus, doctorNotes?: string) =>
    apiClient
      .put<AppointmentItem>(`/appointments/${appointmentId}/status`, { status, doctor_notes: doctorNotes })
      .then((r) => r.data),
  cancel: (appointmentId: string) => apiClient.delete(`/appointments/${appointmentId}`),
};

// ---------- Health tracking ----------
export const medicationRemindersApi = {
  list: () => apiClient.get<PatientMedicationItem[]>("/medication-reminders").then((r) => r.data),
  create: (data: {
    medication_name: string;
    dosage?: string;
    frequency_per_day?: number;
    reminder_times?: string;
    start_date: string;
    end_date?: string;
    notes?: string;
  }) => apiClient.post<PatientMedicationItem>("/medication-reminders", data).then((r) => r.data),
  logDose: (id: string, wasTaken = true) =>
    apiClient.put(`/medication-reminders/${id}/log`, null, { params: { was_taken: wasTaken } }),
  stop: (id: string) => apiClient.delete(`/medication-reminders/${id}`),
};

export const diaryApi = {
  list: () => apiClient.get<SymptomDiaryItem[]>("/diary").then((r) => r.data),
  create: (data: {
    entry_date: string;
    mood_score?: number;
    energy_level?: number;
    pain_level?: number;
    symptoms_text?: string;
    notes?: string;
  }) => apiClient.post<SymptomDiaryItem>("/diary", data).then((r) => r.data),
};

export const vaccinationsApi = {
  list: () => apiClient.get<VaccinationItem[]>("/vaccinations").then((r) => r.data),
  create: (data: {
    vaccine_name: string;
    dose_number?: number;
    date_administered: string;
    next_due_date?: string;
    administered_at?: string;
    notes?: string;
  }) => apiClient.post<VaccinationItem>("/vaccinations", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/vaccinations/${id}`),
};

export const wearablesApi = {
  list: (metricType?: string) =>
    apiClient.get<WearableDataPointItem[]>("/wearables", { params: { metric_type: metricType } }).then((r) => r.data),
  create: (data: { metric_type: string; value: number; recorded_date: string }) =>
    apiClient.post<WearableDataPointItem>("/wearables", data).then((r) => r.data),
  importCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient
      .post<{ imported: number; errors: string[] }>("/wearables/import-csv", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};

// ---------- AI Coach ----------
export const coachApi = {
  nutrition: (goal: string) => apiClient.post<CoachPlan>("/coach/nutrition", { goal }).then((r) => r.data),
  fitness: (goal: string) => apiClient.post<CoachPlan>("/coach/fitness", { goal }).then((r) => r.data),
};

// ---------- Emergency ----------
export const emergencyApi = {
  findHospitals: (lat: number, lon: number, radiusKm = 30, emergencyOnly = false, includeRoute = false) =>
    apiClient
      .get<HospitalItem[]>("/emergency/hospitals", {
        params: { latitude: lat, longitude: lon, radius_km: radiusKm, emergency_only: emergencyOnly, include_route: includeRoute },
      })
      .then((r) => r.data),
  findPharmacies: (lat: number, lon: number, radiusKm = 10, open24hOnly = false, includeRoute = false) =>
    apiClient
      .get<PharmacyItem[]>("/emergency/pharmacies", {
        params: { latitude: lat, longitude: lon, radius_km: radiusKm, open_24h_only: open24hOnly, include_route: includeRoute },
      })
      .then((r) => r.data),
  listContacts: () => apiClient.get<EmergencyContactItem[]>("/emergency/contacts").then((r) => r.data),
  addContact: (data: { name: string; relationship?: string; phone: string; email?: string }) =>
    apiClient.post<EmergencyContactItem>("/emergency/contacts", data).then((r) => r.data),
  deleteContact: (id: string) => apiClient.delete(`/emergency/contacts/${id}`),
  triggerSos: (lat?: number, lon?: number, message?: string) =>
    apiClient.post("/emergency/sos", { latitude: lat, longitude: lon, message }).then((r) => r.data),
};

// ---------- Platform: API keys / referrals / billing / 2FA / privacy ----------
export const apiKeysApi = {
  list: () => apiClient.get<ApiKeyItem[]>("/developer/api-keys").then((r) => r.data),
  create: (name: string) => apiClient.post<ApiKeyCreated>("/developer/api-keys", { name }).then((r) => r.data),
  revoke: (id: string) => apiClient.delete(`/developer/api-keys/${id}`),
};

export const referralsApi = {
  myCode: () => apiClient.get<ReferralCodeData>("/referrals/my-code").then((r) => r.data),
};

export const billingApi = {
  getSubscription: () => apiClient.get<SubscriptionData>("/billing/subscription").then((r) => r.data),
  checkout: () => apiClient.post<{ preview_mode: boolean; checkout_url: string | null; message?: string }>("/billing/checkout").then((r) => r.data),
  cancel: () => apiClient.post("/billing/cancel").then((r) => r.data),
};

export const twoFactorApi = {
  status: () => apiClient.get<{ is_enabled: boolean }>("/2fa/status").then((r) => r.data),
  setup: () => apiClient.post<TwoFactorSetup>("/2fa/setup").then((r) => r.data),
  enable: (code: string) => apiClient.post("/2fa/enable", { code }).then((r) => r.data),
  disable: (code: string) => apiClient.post("/2fa/disable", { code }).then((r) => r.data),
};

export const privacyApi = {
  exportData: () => downloadBlob("/privacy/export"),
  deleteAccount: (password: string) =>
    apiClient.post("/privacy/delete-account", null, { params: { password } }).then((r) => r.data),
};
