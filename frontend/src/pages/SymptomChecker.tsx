import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Download, AlertCircle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { diagnosisApi, familyApi, historyApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { FamilyMember, PredictionOut } from "@/types";
import RiskBadge from "@/components/RiskBadge";
import DisclaimerBanner from "@/components/DisclaimerBanner";

export default function SymptomChecker() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [forMemberId, setForMemberId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionOut | null>(null);

  useEffect(() => { familyApi.list().then(setFamilyMembers).catch(() => {}); }, []);

  async function handleSubmit() {
    if (text.trim().length < 3) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await diagnosisApi.checkSymptoms(text, forMemberId || undefined);
      setResult(data);
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setLoading(false); }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("symptom_checker.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("symptom_checker.subtitle")}</p>
      </div>
      <DisclaimerBanner compact />

      <div className="card">
        {familyMembers.length > 0 && (
          <div className="mb-3">
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("symptom_checker.checking_for")}</label>
            <select value={forMemberId} onChange={(e) => setForMemberId(e.target.value)} className="input-field">
              <option value="">{t("symptom_checker.myself")}</option>
              {familyMembers.map((m) => (
                <option key={m.id} value={m.id}>{m.full_name} ({m.relationship})</option>
              ))}
            </select>
          </div>
        )}
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
          className="input-field resize-none" placeholder={t("symptom_checker.placeholder")} />
        <button onClick={handleSubmit} disabled={loading || text.trim().length < 3} className="btn-primary mt-3 w-full sm:w-auto">
          <Sparkles size={16} />
          {loading ? t("symptom_checker.analyzing") : t("symptom_checker.analyze_btn")}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />{error}
        </div>
      )}

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="card">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("symptom_checker.detected_symptoms")}</h2>
              <RiskBadge level={result.risk_level} />
            </div>
            <div className="flex flex-wrap gap-2">
              {result.explainability.matched_symptoms.map((s) => (
                <span key={s} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">{s}</span>
              ))}
            </div>
          </div>

          <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("symptom_checker.possible_conditions")}</h2>
          {result.results.map((item, idx) => (
            <motion.div key={item.disease_name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="card">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-display text-base font-bold text-slate-900 dark:text-white">{idx + 1}. {item.disease_name}</h3>
                <div className="flex items-center gap-2">
                  <RiskBadge level={item.risk_level} />
                  <span className="text-sm font-bold text-brand-600">{Math.round(item.probability * 100)}%</span>
                </div>
              </div>
              <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">{item.explanation}</p>
              <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
                {item.recommended_specialist && <InfoRow label={t("symptom_checker.recommended_specialist")} value={item.recommended_specialist} />}
                {item.recovery_time_days != null && <InfoRow label={t("symptom_checker.recovery_estimate")} value={`~${item.recovery_time_days} ${t("symptom_checker.days")}`} />}
                {item.home_care_tips && <InfoRow label={t("symptom_checker.home_care")} value={item.home_care_tips} />}
                {item.foods_to_eat && <InfoRow label={t("symptom_checker.foods_to_eat")} value={item.foods_to_eat} />}
                {item.foods_to_avoid && <InfoRow label={t("symptom_checker.foods_to_avoid")} value={item.foods_to_avoid} />}
                {item.when_to_visit_hospital && <InfoRow label={t("symptom_checker.seek_care_if")} value={item.when_to_visit_hospital} />}
              </div>
            </motion.div>
          ))}

          <button onClick={() => historyApi.downloadPdf(result.id)} className="btn-secondary w-full sm:w-auto">
            <Download size={16} />{t("symptom_checker.download_report")}
          </button>
        </motion.div>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-800/50">
      <p className="font-semibold text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-0.5 text-slate-700 dark:text-slate-300">{value}</p>
    </div>
  );
}
