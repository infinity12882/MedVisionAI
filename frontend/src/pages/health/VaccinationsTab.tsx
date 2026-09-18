import { useEffect, useState } from "react";
import { Syringe, Plus, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { vaccinationsApi } from "@/api";
import type { VaccinationItem } from "@/types";

export default function VaccinationsTab() {
  const { t } = useTranslation();
  const [vaccinations, setVaccinations] = useState<VaccinationItem[]>([]);
  const [form, setForm] = useState({ vaccine_name: "", date_administered: new Date().toISOString().slice(0,10), next_due_date: "" });

  function refresh() { vaccinationsApi.list().then(setVaccinations); }
  useEffect(refresh, []);

  async function handleAdd() {
    if (!form.vaccine_name) return;
    try {
      await vaccinationsApi.create({ ...form, next_due_date: form.next_due_date || undefined });
      setForm({ vaccine_name: "", date_administered: new Date().toISOString().slice(0,10), next_due_date: "" });
      refresh();
    } catch (err: any) {
      alert("Failed to add vaccination: " + (err?.response?.data?.detail || "Unknown error"));
    }
  }

  async function handleDelete(id: string) {
    try {
      await vaccinationsApi.delete(id);
      refresh();
    } catch (err: any) {
      alert("Failed to delete vaccination: " + (err?.response?.data?.detail || "Unknown error"));
    }
  }

  const upcoming = vaccinations.filter((v) => v.next_due_date && new Date(v.next_due_date) > new Date());

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("health_tracking.vaccinations.title")}</h2>

      {upcoming.length > 0 && (
        <div className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
          📅 {t("health_tracking.vaccinations.upcoming")} {upcoming.map((v) => `${v.vaccine_name} (${v.next_due_date})`).join(", ")}
        </div>
      )}

      <div className="card flex flex-wrap gap-2">
        <input className="input-field flex-1 min-w-[160px]" placeholder={t("health_tracking.vaccinations.name_placeholder")} value={form.vaccine_name} onChange={(e) => setForm({...form, vaccine_name: e.target.value})} />
        <input type="date" className="input-field" value={form.date_administered} onChange={(e) => setForm({...form, date_administered: e.target.value})} />
        <input type="date" className="input-field" placeholder={t("health_tracking.vaccinations.next_due_placeholder")} value={form.next_due_date} onChange={(e) => setForm({...form, next_due_date: e.target.value})} />
        <button onClick={handleAdd} className="btn-primary"><Plus size={14} /> {t("health_tracking.vaccinations.add_btn")}</button>
      </div>

      {vaccinations.length === 0 ? (
        <p className="text-sm text-slate-400">{t("health_tracking.vaccinations.no_records")}</p>
      ) : vaccinations.map((v) => (
        <div key={v.id} className="card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300"><Syringe size={16} /></div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{v.vaccine_name}</p>
              <p className="text-xs text-slate-500">{t("health_tracking.vaccinations.given")} {v.date_administered}{v.next_due_date && ` · ${t("health_tracking.vaccinations.next_due")} ${v.next_due_date}`}</p>
            </div>
          </div>
          <button onClick={() => handleDelete(v.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button>
        </div>
      ))}
    </div>
  );
}
