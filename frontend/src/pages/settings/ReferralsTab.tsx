import { useEffect, useState } from "react";
import { Gift, Copy, Check, Share2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { referralsApi } from "@/api";
import type { ReferralCodeData } from "@/types";

export default function ReferralsTab() {
  const { t } = useTranslation();
  const [data, setData] = useState<ReferralCodeData | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => { referralsApi.myCode().then(setData).catch(() => {}); }, []);

  function handleCopy() {
    if (!data) return;
    navigator.clipboard.writeText(data.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleShare() {
    if (!data) return;
    const text = `${t("settings.referrals.share_text")} ${window.location.origin}/register?ref=${data.code}`;
    if (navigator.share) {
      navigator.share({ title: t("app_name"), text, url: `${window.location.origin}/register?ref=${data.code}` });
    } else {
      navigator.clipboard.writeText(text);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("settings.referrals.title")}</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("settings.referrals.subtitle")}</p>
      </div>

      {data ? (
        <>
          <div className="rounded-2xl bg-gradient-to-br from-brand-50 to-accent-500/10 p-6 text-center dark:from-brand-950/40 dark:to-accent-900/10">
            <Gift size={36} className="mx-auto mb-3 text-brand-600" />
            <p className="mb-1 text-sm text-slate-500 dark:text-slate-400">{t("settings.referrals.your_code")}</p>
            <p className="font-display text-4xl font-extrabold tracking-widest text-brand-600">{data.code}</p>
            <p className="mt-2 text-xs text-slate-400">{data.uses_count} {t("settings.referrals.uses")}</p>
          </div>

          <div className="flex gap-3">
            <button onClick={handleCopy} className="btn-secondary flex-1">
              {copied ? <Check size={16} className="text-emerald-600" /> : <Copy size={16} />}
              {copied ? t("settings.referrals.copied") : t("settings.referrals.copy_btn")}
            </button>
            <button onClick={handleShare} className="btn-primary flex-1">
              <Share2 size={16} />
              Share
            </button>
          </div>

          <div className="rounded-xl bg-slate-50 p-4 text-xs text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            <p>Registration link:</p>
            <code className="mt-1 block break-all font-mono text-slate-600 dark:text-slate-300">
              {window.location.origin}/register?ref={data.code}
            </code>
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-400">{t("common.loading")}</p>
      )}
    </div>
  );
}
