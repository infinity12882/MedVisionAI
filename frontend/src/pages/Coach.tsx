import { useState } from "react";
import { Dumbbell, Apple, Sparkles, AlertCircle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { coachApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { CoachPlan } from "@/types";

type Mode = "nutrition" | "fitness";

export default function Coach() {
  const { t } = useTranslation();
  const [mode, setMode] = useState<Mode>("nutrition");
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<CoachPlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!goal.trim()) return;
    setLoading(true); setError(null); setPlan(null);
    try {
      const result = mode === "nutrition"
        ? await coachApi.nutrition(goal)
        : await coachApi.fitness(goal);
      setPlan(result);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("coach.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("coach.subtitle")}</p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-3">
        <button
          onClick={() => setMode("nutrition")}
          className={
            mode === "nutrition"
              ? "flex flex-1 items-center justify-center gap-2 rounded-2xl border-2 border-brand-600 bg-brand-50 py-4 text-sm font-bold text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
              : "flex flex-1 items-center justify-center gap-2 rounded-2xl border-2 border-slate-200 py-4 text-sm font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300"
          }
        >
          <Apple size={18} />
          {t("coach.nutrition_title")}
        </button>
        <button
          onClick={() => setMode("fitness")}
          className={
            mode === "fitness"
              ? "flex flex-1 items-center justify-center gap-2 rounded-2xl border-2 border-brand-600 bg-brand-50 py-4 text-sm font-bold text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
              : "flex flex-1 items-center justify-center gap-2 rounded-2xl border-2 border-slate-200 py-4 text-sm font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300"
          }
        >
          <Dumbbell size={18} />
          {t("coach.fitness_title")}
        </button>
      </div>

      {/* Description card */}
      <div className="rounded-xl bg-gradient-to-r from-brand-50 to-accent-500/10 p-4 dark:from-brand-950/40 dark:to-accent-900/10">
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {mode === "nutrition" ? t("coach.nutrition_subtitle") : t("coach.fitness_subtitle")}
        </p>
      </div>

      {/* Input */}
      <div className="card space-y-3">
        <input
          className="input-field"
          placeholder={t("coach.goal_placeholder")}
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
        />
        <button onClick={handleGenerate} disabled={loading || !goal.trim()} className="btn-primary w-full">
          <Sparkles size={16} />
          {loading
            ? t("coach.generating")
            : mode === "nutrition"
              ? t("coach.generate_nutrition")
              : t("coach.generate_fitness")}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />{error}
        </div>
      )}

      {plan && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
          {plan.used_fallback && (
            <div className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-950/30 dark:text-amber-300">
              {t("coach.fallback_note")}
            </div>
          )}
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {plan.plan.split("\n").map((line, i) => (
              <p key={i} className={
                line.startsWith("**") && line.endsWith("**")
                  ? "mt-4 font-display text-base font-bold text-slate-900 dark:text-white"
                  : line.startsWith("-") || line.startsWith("•")
                    ? "ml-2 text-sm text-slate-700 dark:text-slate-300"
                    : "text-sm text-slate-600 dark:text-slate-400"
              }>
                {line.replace(/\*\*/g, "")}
              </p>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
