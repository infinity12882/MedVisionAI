import { useEffect, useRef, useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from "chart.js";
import { Plus, Upload } from "lucide-react";
import { useTranslation } from "react-i18next";
import { wearablesApi } from "@/api";
import type { WearableDataPointItem } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const METRICS = ["steps", "heart_rate", "sleep_hours", "calories", "weight_kg"];
const COLORS: Record<string, string> = {
  steps: "#0f9684", heart_rate: "#ef4444", sleep_hours: "#6366f1",
  calories: "#f59e0b", weight_kg: "#8b5cf6",
};

export default function WearablesTab() {
  const { t } = useTranslation();
  const [data, setData] = useState<WearableDataPointItem[]>([]);
  const [metric, setMetric] = useState("steps");
  const [form, setForm] = useState({ metric_type: "steps", value: "", recorded_date: new Date().toISOString().slice(0, 10) });
  const [importing, setImporting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function refresh() {
    wearablesApi.list(metric).then(setData).catch(() => {});
  }
  useEffect(refresh, [metric]);

  async function handleAdd() {
    if (!form.value) return;
    await wearablesApi.create({ metric_type: metric, value: Number(form.value), recorded_date: form.recorded_date });
    setForm({ ...form, value: "" });
    refresh();
  }

  async function handleImport(file: File) {
    setImporting(true);
    try {
      const result = await wearablesApi.importCsv(file);
      alert(`Imported ${result.imported} rows${result.errors.length ? `. Errors: ${result.errors.slice(0, 3).join("; ")}` : ""}`);
      refresh();
    } finally { setImporting(false); }
  }

  const sorted = [...data].sort((a, b) => a.recorded_date.localeCompare(b.recorded_date)).slice(-30);

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("health_tracking.wearables.title")}</h2>

      <div className="flex flex-wrap gap-2">
        {METRICS.map((m) => (
          <button key={m} onClick={() => setMetric(m)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
              metric === m
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {t(`health_tracking.wearables.metrics.${m}`)}
          </button>
        ))}
      </div>

      {sorted.length > 1 && (
        <div className="card">
          <Line
            data={{
              labels: sorted.map((d) => d.recorded_date.slice(5)),
              datasets: [{
                label: t(`health_tracking.wearables.metrics.${metric}`),
                data: sorted.map((d) => d.value),
                borderColor: COLORS[metric] || "#0f9684",
                backgroundColor: (COLORS[metric] || "#0f9684") + "22",
                fill: true, tension: 0.3,
              }],
            }}
            options={{ plugins: { legend: { display: false } }, scales: { y: { beginAtZero: metric !== "weight_kg" } } }}
            height={80}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <input className="input-field flex-1 min-w-[120px]" type="number" placeholder={t("health_tracking.wearables.value_placeholder")}
          value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
        <input className="input-field" type="date" value={form.recorded_date}
          onChange={(e) => setForm({ ...form, recorded_date: e.target.value })} />
        <button onClick={handleAdd} className="btn-primary"><Plus size={14} />{t("health_tracking.wearables.add_btn")}</button>
        <button onClick={() => fileRef.current?.click()} disabled={importing} className="btn-secondary">
          <Upload size={14} />{t("health_tracking.wearables.import_csv")}
        </button>
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => e.target.files?.[0] && handleImport(e.target.files[0])} />
      </div>

      {data.length === 0 ? (
        <p className="text-sm text-slate-400">{t("health_tracking.wearables.no_data")}</p>
      ) : (
        <div className="space-y-2">
          {[...data].sort((a, b) => b.recorded_date.localeCompare(a.recorded_date)).slice(0, 10).map((d) => (
            <div key={d.id} className="card flex items-center justify-between text-sm">
              <span className="text-slate-500">{d.recorded_date}</span>
              <span className="font-bold" style={{ color: COLORS[d.metric_type] }}>{d.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
