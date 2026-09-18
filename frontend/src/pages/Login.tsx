import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Activity, Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import { login } from "@/store/slices/authSlice";
import { extractErrorMessage } from "@/api/client";

export default function Login() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { status } = useAppSelector((s) => s.auth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [needTotp, setNeedTotp] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await dispatch(login({ email, password, totp_code: needTotp ? totpCode : undefined })).unwrap();
      navigate("/dashboard");
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      if (err === "2FA_REQUIRED" || msg === "2FA_REQUIRED") {
        setNeedTotp(true);
        setError(null);
      } else {
        setError(msg);
      }
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 dark:from-slate-950 dark:to-slate-950">
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
          {t("auth.welcome_back")}
        </h1>
        <p className="mb-6 text-center text-sm text-slate-500 dark:text-slate-400">{t("auth.login_subtitle")}</p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!needTotp ? (
            <>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.email")}</label>
                <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="you@example.com" />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.password")}</label>
                <div className="relative">
                  <input type={showPassword ? "text" : "password"} required value={password} onChange={(e) => setPassword(e.target.value)} className="input-field pr-10" placeholder="••••••••" />
                  <button type="button" onClick={() => setShowPassword((s) => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div>
              <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">{t("auth.two_fa_required")}</p>
              <input type="text" inputMode="numeric" maxLength={6} value={totpCode} onChange={(e) => setTotpCode(e.target.value)} className="input-field text-center text-2xl tracking-widest" placeholder="000000" autoFocus />
            </div>
          )}

          <button type="submit" disabled={status === "loading"} className="btn-primary w-full">
            {status === "loading" ? t("auth.logging_in") : t("auth.login_btn")}
          </button>

          <div className="text-center">
            <Link to="#" className="text-sm font-medium text-brand-600 hover:underline">Forgot password?</Link>
          </div>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          {t("auth.no_account")}{" "}
          <Link to="/register" className="font-semibold text-brand-600 hover:underline">{t("auth.sign_up")}</Link>
        </p>

        <div className="mt-6 rounded-xl bg-slate-50 p-3 text-xs text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
          <p className="mb-1 font-semibold">{t("auth.demo_accounts")}:</p>
          <p>admin@medvision.ai / Admin@12345</p>
          <p>doctor@medvision.ai / Doctor@12345</p>
          <p>patient@medvision.ai / Patient@12345</p>
        </div>
      </motion.div>
    </div>
  );
}
