import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Activity } from "lucide-react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import { register } from "@/store/slices/authSlice";
import { extractErrorMessage } from "@/api/client";
import type { UserRole } from "@/types";

export default function Register() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { status } = useAppSelector((s) => s.auth);
  const [form, setForm] = useState({
    full_name: "", email: "", password: "",
    role: "patient" as UserRole, referral_code: searchParams.get("ref") || "",
  });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await dispatch(register(form)).unwrap();
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 py-10 dark:from-slate-950 dark:to-slate-950">
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="glass-panel w-full max-w-md p-8"
      >
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Activity size={20} />
          </div>
          <span className="font-display text-xl font-bold text-slate-900 dark:text-white">{t("app_name")}</span>
        </Link>

        <h1 className="mb-1 text-center font-display text-2xl font-bold text-slate-900 dark:text-white">
          {t("auth.register_title")}
        </h1>
        <p className="mb-6 text-center text-sm text-slate-500 dark:text-slate-400">{t("auth.register_subtitle")}</p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.full_name")}</label>
            <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="input-field" placeholder="Jane Doe" />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.email")}</label>
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-field" />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.password")}</label>
            <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input-field" placeholder="Min 8 characters" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.iam_a")}</label>
            <div className="grid grid-cols-2 gap-2">
              {(["patient", "doctor"] as UserRole[]).map((role) => (
                <button key={role} type="button" onClick={() => setForm({ ...form, role })}
                  className={form.role === role
                    ? "rounded-xl border-2 border-brand-600 bg-brand-50 px-4 py-2.5 text-sm font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                    : "rounded-xl border-2 border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300"
                  }
                >
                  {role === "patient" ? t("auth.patient") : t("auth.doctor")}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.referral_code")}</label>
            <input value={form.referral_code} onChange={(e) => setForm({ ...form, referral_code: e.target.value })} className="input-field" placeholder="ABC12345" />
          </div>

          <button type="submit" disabled={status === "loading"} className="btn-primary w-full">
            {status === "loading" ? t("auth.creating_account") : t("auth.register_btn")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("auth.have_account")}{" "}
          <Link to="/login" className="font-semibold text-brand-600 hover:underline">{t("auth.sign_in")}</Link>
        </p>
      </motion.div>
    </div>
  );
}
