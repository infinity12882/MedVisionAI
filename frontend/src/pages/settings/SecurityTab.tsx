import { useEffect, useState } from "react";
import { Shield, ShieldCheck, ShieldOff } from "lucide-react";
import { useTranslation } from "react-i18next";
import { twoFactorApi } from "@/api";
import type { TwoFactorSetup } from "@/types";

export default function SecurityTab() {
  const { t } = useTranslation();
  const [is2faEnabled, setIs2faEnabled] = useState(false);
  const [setup, setSetup] = useState<TwoFactorSetup | null>(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    twoFactorApi.status().then((s) => setIs2faEnabled(s.is_enabled)).catch(() => {});
  }, []);

  async function handleSetup() {
    setLoading(true); setMsg(null);
    try {
      const data = await twoFactorApi.setup();
      setSetup(data);
    } catch { setMsg({ type: "err", text: "Setup failed" }); }
    finally { setLoading(false); }
  }

  async function handleEnable() {
    if (!code.trim()) return;
    setLoading(true); setMsg(null);
    try {
      await twoFactorApi.enable(code);
      setIs2faEnabled(true);
      setSetup(null);
      setCode("");
      setMsg({ type: "ok", text: t("common.success") });
    } catch { setMsg({ type: "err", text: "Invalid code" }); }
    finally { setLoading(false); }
  }

  async function handleDisable() {
    if (!code.trim()) return;
    setLoading(true); setMsg(null);
    try {
      await twoFactorApi.disable(code);
      setIs2faEnabled(false);
      setCode("");
      setMsg({ type: "ok", text: "2FA disabled" });
    } catch { setMsg({ type: "err", text: "Invalid code" }); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("settings.two_fa.title")}</h2>

      <div className="card flex items-center justify-between">
        <div className="flex items-center gap-3">
          {is2faEnabled
            ? <ShieldCheck size={22} className="text-emerald-600" />
            : <ShieldOff size={22} className="text-slate-400" />}
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-200">
              {is2faEnabled ? t("settings.two_fa.enabled") : t("settings.two_fa.disabled")}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">TOTP (Google Authenticator, Authy, 1Password)</p>
          </div>
        </div>
        {!is2faEnabled && !setup && (
          <button onClick={handleSetup} disabled={loading} className="btn-primary text-sm">
            {t("settings.two_fa.enable_btn")}
          </button>
        )}
      </div>

      {setup && (
        <div className="card space-y-4">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{t("settings.two_fa.setup_title")}</p>
          <div className="flex justify-center">
            <img src={setup.qr_code_data_url} alt="QR Code" className="h-48 w-48 rounded-xl" />
          </div>
          <div>
            <p className="mb-2 text-xs font-semibold text-slate-500">{t("settings.two_fa.backup_codes")}</p>
            <div className="grid grid-cols-2 gap-1.5 rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
              {setup.backup_codes.map((code) => (
                <code key={code} className="rounded bg-white px-2 py-1 text-xs font-mono text-slate-700 dark:bg-slate-800 dark:text-slate-300">{code}</code>
              ))}
            </div>
          </div>
          <input
            className="input-field text-center text-xl tracking-widest"
            placeholder={t("settings.two_fa.verify_placeholder")}
            value={code} onChange={(e) => setCode(e.target.value)}
            maxLength={6} inputMode="numeric"
          />
          <button onClick={handleEnable} disabled={loading || code.length !== 6} className="btn-primary w-full">
            {t("settings.two_fa.verify_btn")}
          </button>
        </div>
      )}

      {is2faEnabled && (
        <div className="card space-y-3">
          <p className="text-sm text-slate-600 dark:text-slate-400">{t("settings.two_fa.confirm_disable")}</p>
          <input
            className="input-field text-center text-xl tracking-widest"
            placeholder={t("settings.two_fa.verify_placeholder")}
            value={code} onChange={(e) => setCode(e.target.value)}
            maxLength={6} inputMode="numeric"
          />
          <button onClick={handleDisable} disabled={loading || code.length !== 6}
            className="rounded-xl border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800">
            {t("settings.two_fa.disable_btn")}
          </button>
        </div>
      )}

      {msg && (
        <p className={`text-sm ${msg.type === "ok" ? "text-emerald-600" : "text-red-600"}`}>{msg.text}</p>
      )}
    </div>
  );
}
