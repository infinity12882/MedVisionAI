import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Activity, Stethoscope, Camera, Mic, MessageCircle, ShieldCheck, Brain, ArrowRight } from "lucide-react";
import { setLanguage, toggleDarkMode } from "@/store/slices/uiSlice";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import clsx from "clsx";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "uz", label: "UZ" },
  { code: "ru", label: "RU" },
];

export default function Landing() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const { darkMode, language } = useAppSelector((s) => s.ui);

  function handleLang(lang: string) {
    dispatch(setLanguage(lang as "en" | "uz" | "ru"));
    i18n.changeLanguage(lang);
  }

  const FEATURES = [
    { icon: Stethoscope, title: t("landing.features.text_checker"), desc: t("landing.features.text_desc") },
    { icon: Camera,      title: t("landing.features.image_diag"),   desc: t("landing.features.image_desc") },
    { icon: Mic,         title: t("landing.features.voice_diag"),   desc: t("landing.features.voice_desc") },
    { icon: MessageCircle, title: t("landing.features.ai_chat"),    desc: t("landing.features.ai_desc") },
    { icon: Brain,       title: t("landing.features.explainable"),  desc: t("landing.features.explainable_desc") },
    { icon: ShieldCheck, title: t("landing.features.rag"),          desc: t("landing.features.rag_desc") },
  ];

  return (
    <div className="min-h-screen overflow-hidden bg-gradient-to-b from-brand-50 via-white to-white dark:from-slate-950 dark:via-slate-950 dark:to-slate-950">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Activity size={20} />
          </div>
          <span className="font-display text-xl font-bold text-slate-900 dark:text-white">{t("app_name")}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
            {LANGS.map((l) => (
              <button
                key={l.code}
                onClick={() => handleLang(l.code)}
                className={clsx(
                  "px-2.5 py-1.5 text-xs font-bold transition-colors",
                  language === l.code
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                )}
              >
                {l.label}
              </button>
            ))}
          </div>
          <Link to="/login" className="btn-ghost text-sm">{t("nav.login")}</Link>
          <Link to="/register" className="btn-primary text-sm">{t("nav.register")}</Link>
        </div>
      </header>

      <section className="relative mx-auto max-w-5xl px-6 pb-20 pt-16 text-center sm:pt-24">
        <div className="pointer-events-none absolute -top-20 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-brand-300/30 blur-3xl animate-float" />
        <motion.h1
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          className="font-display text-4xl font-extrabold leading-tight text-slate-900 dark:text-white sm:text-6xl"
        >
          {t("landing.title_1")}<br />
          <span className="bg-gradient-to-r from-brand-600 to-accent-600 bg-clip-text text-transparent">
            {t("landing.title_2")}
          </span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-400"
        >
          {t("tagline")}
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Link to="/register" className="btn-primary px-8 py-3 text-base">
            {t("landing.get_started")} <ArrowRight size={18} />
          </Link>
          <Link to="/login" className="btn-secondary px-8 py-3 text-base">
            {t("landing.already_have_account")}
          </Link>
        </motion.div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-24">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ duration: 0.4, delay: i * 0.05 }}
              className="glass-panel p-6"
            >
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                <f.icon size={22} />
              </div>
              <h3 className="mb-2 font-display text-lg font-bold text-slate-900 dark:text-white">{f.title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="border-t border-slate-200 px-6 py-8 text-center text-sm text-slate-500 dark:border-slate-800">
        <p className="mx-auto max-w-3xl">{t("disclaimer")}</p>
        <p className="mt-3">© {new Date().getFullYear()} MedVision AI</p>
      </footer>
    </div>
  );
}
