import { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from "chart.js";
import { Download, Stethoscope, Camera, Mic, FileText, Notebook } from "lucide-react";
import { historyApi } from "@/api";
import type { HistoryItem } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const ICONS: Record<string, typeof Stethoscope> = {
  prediction: Stethoscope,
  image: Camera,
  voice: Mic,
  lab_report: FileText,
  note: Notebook,
};

export default function History() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    historyApi
      .list()
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  const chartData = useMemo(() => {
    const byDay = new Map<string, number>();
    for (const item of items) {
      const day = new Date(item.created_at).toLocaleDateString();
      byDay.set(day, (byDay.get(day) ?? 0) + 1);
    }
    const labels = Array.from(byDay.keys()).reverse();
    const data = Array.from(byDay.values()).reverse();
    return { labels, data };
  }, [items]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">My Medical History</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          A timeline of every AI analysis you've run on MedVision AI.
        </p>
      </div>

      {items.length > 0 && (
        <div className="card">
          <h2 className="mb-3 font-display text-base font-bold text-slate-900 dark:text-white">Activity Over Time</h2>
          <Line
            data={{
              labels: chartData.labels,
              datasets: [
                {
                  label: "Checks",
                  data: chartData.data,
                  borderColor: "#0f9684",
                  backgroundColor: "rgba(23,184,156,0.15)",
                  fill: true,
                  tension: 0.35,
                },
              ],
            }}
            options={{
              plugins: { legend: { display: false } },
              scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            }}
            height={80}
          />
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Loading...</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-400">No history yet. Try the symptom checker to get started.</p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const Icon = ICONS[item.event_type] ?? Notebook;
            return (
              <div key={item.id} className="card flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300">
                  <Icon size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{item.title}</p>
                  {item.detail && (
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{item.detail}</p>
                  )}
                  <p className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
                </div>
                {item.prediction_id && (
                  <button
                    onClick={() => historyApi.downloadPdf(item.prediction_id!)}
                    className="btn-ghost shrink-0 text-xs"
                  >
                    <Download size={14} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
