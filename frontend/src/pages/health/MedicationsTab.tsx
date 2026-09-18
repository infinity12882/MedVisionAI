import { useEffect, useState } from "react";
import { Pill, Plus, Check, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { medicationRemindersApi } from "@/api";
import type { PatientMedicationItem } from "@/types";

export default function MedicationsTab() {
  const { t } = useTranslation();
  const [meds, setMeds] = useState<PatientMedicationItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    medication_name: "", dosage: "", frequency_per_day: 1,
    reminder_times: "09:00", start_date: new Date().toISOString().slice(0, 10),
  });

  function refresh() { medicationRemindersApi.list().then(setMeds); }
  useEffect(refresh, []);

  async function handleAdd() {
    try {
      await medicationRemindersApi.create(form);
      setShowForm(false);
      setForm({ medication_name:"", dosage:"", frequency_per_day:1, reminder_times:"09:00", start_date: new Date().toISOString().slice(0,10) });
      refresh();
    } catch (err: any) {
      alert("Failed to add medication: " + (err?.response?.data?.detail || "Unknown error"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("health_tracking.medications.title")}</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          <Plus size={14} /> {t("health_tracking.medications.add_btn")}
        </button>
      </div>

      {showForm && (
        <div className="card grid grid-cols-1 gap-2 sm:grid-cols-2">
          <input className="input-field" placeholder={t("health_tracking.medications.name_placeholder")} value={form.medication_name} onChange={(e) => setForm({...form, medication_name: e.target.value})} />
          <input className="input-field" placeholder={t("health_tracking.medications.dosage_placeholder")} value={form.dosage} onChange={(e) => setForm({...form, dosage: e.target.value})} />
          <input className="input-field" placeholder={t("health_tracking.medications.reminder_placeholder")} value={form.reminder_times} onChange={(e) => setForm({...form, reminder_times: e.target.value})} />
          <input type="date" className="input-field" value={form.start_date} onChange={(e) => setForm({...form, start_date: e.target.value})} />
          <button onClick={handleAdd} disabled={!form.medication_name} className="btn-primary sm:col-span-2">
            {t("health_tracking.medications.save_btn")}
          </button>
        </div>
      )}

      {meds.length === 0 ? (
        <p className="text-sm text-slate-400">{t("health_tracking.medications.no_meds")}</p>
      ) : (
        <div className="space-y-3">
          {meds.map((m) => (
            <div key={m.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300">
                  <Pill size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{m.medication_name}</p>
                  <p className="text-xs text-slate-500">{m.dosage && `${m.dosage} · `}{m.reminder_times}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => medicationRemindersApi.logDose(m.id, true)} className="btn-secondary text-xs">
                  <Check size={13} /> {t("health_tracking.medications.taken_btn")}
                </button>
                <button onClick={() => medicationRemindersApi.stop(m.id).then(refresh)} className="text-red-400 hover:text-red-600">
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
