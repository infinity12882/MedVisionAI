import { useEffect, useState } from "react";
import { Crown, Check, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { billingApi } from "@/api";
import type { SubscriptionData } from "@/types";

export default function SubscriptionTab() {
  const { t } = useTranslation();
  const [sub, setSub] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => { billingApi.getSubscription().then(setSub).catch(() => {}); }, []);

  async function handleUpgrade() {
    setLoading(true); setMsg(null);
    try {
      const result = await billingApi.checkout();
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      } else {
        setMsg(result.message || t("settings.subscription.preview_note"));
        billingApi.getSubscription().then(setSub);
      }
    } finally { setLoading(false); }
  }

  async function handleCancel() {
    if (!confirm("Cancel your Premium subscription?")) return;
    setLoading(true);
    try {
      await billingApi.cancel();
      billingApi.getSubscription().then(setSub);
    } finally { setLoading(false); }
  }

  const freeBenefits: string[] = t("settings.subscription.benefits.free", { returnObjects: true }) as string[];
  const premiumBenefits: string[] = t("settings.subscription.benefits.premium", { returnObjects: true }) as string[];

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("settings.tabs.subscription")}</h2>

      {sub && (
        <div className={`card flex items-center justify-between ${sub.tier === "premium" ? "border-brand-300 dark:border-brand-700" : ""}`}>
          <div className="flex items-center gap-3">
            {sub.tier === "premium" && <Crown size={20} className="text-amber-500" />}
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-200">
                {t("settings.subscription.current_tier")}:{" "}
                <span className={sub.tier === "premium" ? "text-amber-600" : "text-slate-600"}>
                  {sub.tier === "premium" ? t("settings.subscription.premium") : t("settings.subscription.free")}
                </span>
              </p>
              {sub.current_period_end && (
                <p className="text-xs text-slate-500">
                  Active until: {new Date(sub.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {msg && (
        <div className="rounded-lg bg-amber-50 px-4 py-2.5 text-sm text-amber-700 dark:bg-amber-950/30 dark:text-amber-300">
          {msg}
        </div>
      )}

      {/* Plan comparison */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Free */}
        <div className={`card ${sub?.tier === "free" ? "border-2 border-slate-300 dark:border-slate-600" : ""}`}>
          <p className="mb-3 font-display text-lg font-bold text-slate-900 dark:text-white">
            {t("settings.subscription.free")}
          </p>
          <p className="mb-4 text-2xl font-extrabold text-slate-900 dark:text-white">$0<span className="text-sm font-normal text-slate-500">/mo</span></p>
          <ul className="space-y-2">
            {freeBenefits.map((b) => (
              <li key={b} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                <Check size={14} className="mt-0.5 shrink-0 text-emerald-500" />{b}
              </li>
            ))}
          </ul>
        </div>

        {/* Premium */}
        <div className={`card ${sub?.tier === "premium" ? "border-2 border-brand-400 dark:border-brand-600" : ""}`}>
          <div className="mb-3 flex items-center gap-2">
            <Crown size={18} className="text-amber-500" />
            <p className="font-display text-lg font-bold text-slate-900 dark:text-white">
              {t("settings.subscription.premium")}
            </p>
          </div>
          <p className="mb-4 text-2xl font-extrabold text-slate-900 dark:text-white">$9.99<span className="text-sm font-normal text-slate-500">/mo</span></p>
          <ul className="mb-4 space-y-2">
            {premiumBenefits.map((b) => (
              <li key={b} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                <Check size={14} className="mt-0.5 shrink-0 text-emerald-500" />{b}
              </li>
            ))}
          </ul>
          {sub?.tier !== "premium" && (
            <button onClick={handleUpgrade} disabled={loading} className="btn-primary w-full">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Crown size={16} />}
              {t("settings.subscription.upgrade_btn")}
            </button>
          )}
          {sub?.tier === "premium" && (
            <button onClick={handleCancel} disabled={loading}
              className="w-full rounded-xl border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800">
              {t("settings.subscription.cancel_btn")}
            </button>
          )}
        </div>
      </div>

      {!sub?.is_stripe_configured && (
        <p className="text-xs text-slate-400">{t("settings.subscription.preview_note")}</p>
      )}
    </div>
  );
}
