import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip } from "chart.js";
import { Stethoscope, Camera, Mic, MessageCircle, Droplets, Moon, Activity, Dumbbell } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAppSelector } from "@/hooks/redux";
import { usersApi, historyApi } from "@/api";
import type { HealthScoreOut, HistoryItem } from "@/types";
import DisclaimerBanner from "@/components/DisclaimerBanner";

ChartJS.register(ArcElement, Tooltip);

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAppSelector((s) => s.auth);
  const [healthScore, setHealthScore] = useState<HealthScoreOut | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const QUICK_ACTIONS = [
    { to: "/symptom-checker", icon: Stethoscope, key: "dashboard.check_symptoms",  color: "bg-brand-600" },
    { to: "/image-diagnosis",  icon: Camera,      key: "dashboard.analyze_image",   color: "bg-accent-600" },
    { to: "/voice-diagnosis",  icon: Mic,         key: "dashboard.voice_check",     color: "bg-rose-500" },
    { to: "/chat",             icon: MessageCircle,key:"dashboard.ask_ai_chat",     color: "bg-amber-500" },
  ];

  useEffect(() => {
    async function load() {
      try {
        const h = await historyApi.list();
        setHistory(h.slice(0, 5));
        if (user?.role === "patient") {
          const score = await usersApi.getHealthScore();
          setHealthScore(score);
        }
      } catch { /* non-fatal */ }
      finally { setLoading(false); }
    }
    load();
  }, [user]);

  const scoreColor = healthScore
    ? healthScore.overall_score >= 80 ? "#10b981"
      : healthScore.overall_score >= 55 ? "#f59e0b" : "#ef4444"
    : "#94a3b8";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">
          {t("dashboard.welcome")}, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("dashboard.health_overview")}</p>
      </div>

      <DisclaimerBanner compact />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {QUICK_ACTIONS.map((action, i) => (
          <motion.div key={action.to} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Link to={action.to} className="card flex flex-col items-center gap-3 p-5 text-center hover:shadow-md transition-shadow">
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${action.color} text-white`}>
                <action.icon size={20} />
              </div>
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t(action.key)}</span>
            </Link>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {user?.role === "patient" && (
          <div className="card lg:col-span-1">
            <h2 className="mb-4 font-display text-lg font-bold text-slate-900 dark:text-white">{t("dashboard.health_score")}</h2>
            {loading ? (
              <div className="flex h-48 items-center justify-center text-slate-400">{t("dashboard.loading")}</div>
            ) : healthScore ? (
              <>
                <div className="relative mx-auto h-44 w-44">
                  <Doughnut
                    data={{ datasets: [{ data: [healthScore.overall_score, 100 - healthScore.overall_score], backgroundColor: [scoreColor, "#e2e8f0"], borderWidth: 0 }] }}
                    options={{ cutout: "75%", plugins: { tooltip: { enabled: false }, legend: { display: false } } }}
                  />
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="font-display text-3xl font-extrabold text-slate-900 dark:text-white">{healthScore.overall_score}</span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">{t("dashboard.out_of_100")}</span>
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3 text-xs">
                  <ScoreRow icon={Moon}     label={t("dashboard.sleep")}     value={healthScore.sleep_score} />
                  <ScoreRow icon={Droplets} label={t("dashboard.hydration")} value={healthScore.water_intake_score} />
                  <ScoreRow icon={Activity} label={t("dashboard.stress")}    value={healthScore.stress_score} />
                  <ScoreRow icon={Dumbbell} label={t("dashboard.exercise")}  value={healthScore.exercise_score} />
                </div>
                {healthScore.bmi && (
                  <p className="mt-4 text-xs text-slate-500">BMI: <span className="font-semibold">{healthScore.bmi}</span> ({healthScore.bmi_category})</p>
                )}
                <Link to="/profile" className="mt-4 block text-center text-xs font-semibold text-brand-600 hover:underline">
                  {t("dashboard.update_lifestyle")}
                </Link>
              </>
            ) : <p className="text-sm text-slate-500">{t("dashboard.no_activity")}</p>}
          </div>
        )}

        <div className={user?.role === "patient" ? "card lg:col-span-2" : "card lg:col-span-3"}>
          <h2 className="mb-4 font-display text-lg font-bold text-slate-900 dark:text-white">{t("dashboard.recent_activity")}</h2>
          {history.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">{t("dashboard.no_activity")}</p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {history.map((item) => (
                <li key={item.id} className="flex items-start gap-3 py-3">
                  <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-brand-500" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{item.title}</p>
                    <p className="text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function ScoreRow({ icon: Icon, label, value }: { icon: typeof Moon; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
      <Icon size={14} className="text-brand-600 dark:text-brand-400" />
      <div className="flex-1">
        <p className="text-slate-500 dark:text-slate-400">{label}</p>
        <p className="font-semibold text-slate-800 dark:text-slate-200">{Math.round(value)}/100</p>
      </div>
    </div>
  );
}
