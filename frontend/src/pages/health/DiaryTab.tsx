import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from "chart.js";
import { useTranslation } from "react-i18next";
import { diaryApi } from "@/api";
import type { SymptomDiaryItem } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export default function DiaryTab() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<SymptomDiaryItem[]>([]);
  const [form, setForm] = useState({
    entry_date: new Date().toISOString().slice(0,10),
    mood_score: 3, energy_level: 3, pain_level: 0,
    symptoms_text: "", notes: "",
  });

  function refresh() { diaryApi.list().then(setEntries); }
  useEffect(refresh, []);

  async function handleSave() { 
    try {
      await diaryApi.create(form); 
      refresh(); 
    } catch (err: any) {
      alert("Failed to save diary entry: " + (err?.response?.data?.detail || "Unknown error"));
    }
  }

  const chartEntries = [...entries].reverse().slice(-14);

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("health_tracking.diary.title")}</h2>

      <div className="card space-y-3">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">Date</label>
            <input type="date" className="input-field" value={form.entry_date} onChange={(e) => setForm({...form, entry_date: e.target.value})} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">{t("health_tracking.diary.mood")}</label>
            <input type="number" min={1} max={5} className="input-field" value={form.mood_score} onChange={(e) => setForm({...form, mood_score: Number(e.target.value)})} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">{t("health_tracking.diary.energy")}</label>
            <input type="number" min={1} max={5} className="input-field" value={form.energy_level} onChange={(e) => setForm({...form, energy_level: Number(e.target.value)})} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">{t("health_tracking.diary.pain")}</label>
            <input type="number" min={0} max={10} className="input-field" value={form.pain_level} onChange={(e) => setForm({...form, pain_level: Number(e.target.value)})} />
          </div>
        </div>
        <textarea className="input-field" placeholder={t("health_tracking.diary.text_placeholder")} rows={2}
          value={form.symptoms_text} onChange={(e) => setForm({...form, symptoms_text: e.target.value})} />
        <button onClick={handleSave} className="btn-primary">{t("health_tracking.diary.save_btn")}</button>
      </div>

      {chartEntries.length > 1 && (
        <div className="card">
          <h3 className="mb-3 text-sm font-bold text-slate-900 dark:text-white">{t("health_tracking.diary.trend_title")}</h3>
          <Line
            data={{
              labels: chartEntries.map((e) => e.entry_date.slice(5)),
              datasets: [
                { label: t("health_tracking.diary.mood"),   data: chartEntries.map((e) => e.mood_score),   borderColor: "#0f9684", tension: 0.3 },
                { label: t("health_tracking.diary.energy"), data: chartEntries.map((e) => e.energy_level), borderColor: "#6366f1", tension: 0.3 },
                { label: t("health_tracking.diary.pain"),   data: chartEntries.map((e) => e.pain_level),   borderColor: "#ef4444", tension: 0.3 },
              ],
            }}
            options={{ scales: { y: { beginAtZero: true } } }}
            height={80}
          />
        </div>
      )}

      <div className="space-y-2">
        {entries.slice(0, 10).map((e) => (
          <div key={e.id} className="card flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-300">{e.entry_date}</span>
            <span className="text-xs text-slate-500">
              {t("health_tracking.diary.mood")} {e.mood_score ?? "—"} · {t("health_tracking.diary.energy")} {e.energy_level ?? "—"} · {t("health_tracking.diary.pain")} {e.pain_level ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
