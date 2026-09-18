import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from "chart.js";
import { useTranslation } from "react-i18next";
import { Users, Stethoscope, Pill, FileText, Image as ImageIcon, Mic, CheckCircle2 } from "lucide-react";
import { adminApi } from "@/api";
import type { DatasetAnalytics } from "@/types";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export default function AdminOverview() {
  const { t } = useTranslation();
  const [data, setData] = useState<DatasetAnalytics | null>(null);

  useEffect(() => { adminApi.analytics().then(setData); }, []);

  if (!data) return <p className="text-sm text-slate-400">{t("common.loading")}</p>;

  const STAT_CARDS = [
    { key: "total_diseases"       as const, label: t("admin.analytics.diseases"),       icon: Stethoscope, color: "bg-brand-600"   },
    { key: "total_symptoms"       as const, label: t("admin.analytics.symptoms"),       icon: Stethoscope, color: "bg-accent-600"  },
    { key: "total_medications"    as const, label: t("admin.analytics.medications"),    icon: Pill,        color: "bg-rose-500"    },
    { key: "total_articles"       as const, label: t("admin.analytics.articles"),       icon: FileText,    color: "bg-amber-500"   },
    { key: "total_images"         as const, label: t("admin.analytics.images"),         icon: ImageIcon,   color: "bg-emerald-500" },
    { key: "total_voice_records"  as const, label: t("admin.analytics.voice_records"),  icon: Mic,         color: "bg-indigo-500"  },
    { key: "total_verified_cases" as const, label: t("admin.analytics.verified_cases"), icon: CheckCircle2,color: "bg-teal-600"    },
    { key: "total_users"          as const, label: t("admin.analytics.total_users"),    icon: Users,       color: "bg-slate-700"   },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {STAT_CARDS.map((card) => (
          <div key={card.key} className="card">
            <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${card.color} text-white`}>
              <card.icon size={16} />
            </div>
            <p className="font-display text-2xl font-bold text-slate-900 dark:text-white">{data[card.key]}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{card.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="card">
          <p className="mb-2 text-xs font-semibold text-slate-500">{t("admin.analytics.predictions_week")}</p>
          <Bar
            data={{ labels: data.predictions_last_7_days.map((d) => d.date.slice(5)), datasets: [{ data: data.predictions_last_7_days.map((d) => d.count), backgroundColor: "#0f9684" }] }}
            options={{ plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }}
            height={120}
          />
        </div>
        <div className="card">
          <p className="mb-2 text-xs font-semibold text-slate-500">{t("admin.analytics.doctors")} / {t("admin.analytics.patients")}</p>
          <div className="flex items-center gap-8 py-4">
            <div className="text-center"><p className="font-display text-3xl font-bold text-brand-600">{data.total_doctors}</p><p className="text-xs text-slate-500">{t("admin.analytics.doctors")}</p></div>
            <div className="text-center"><p className="font-display text-3xl font-bold text-accent-600">{data.total_patients}</p><p className="text-xs text-slate-500">{t("admin.analytics.patients")}</p></div>
          </div>
        </div>
      </div>
    </div>
  );
}
