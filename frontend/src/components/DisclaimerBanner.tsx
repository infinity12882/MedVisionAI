import { ShieldAlert } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  return (
    <div className={compact
      ? "flex items-start gap-2 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 px-3 py-2 text-xs text-amber-800 dark:text-amber-300"
      : "flex items-start gap-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 px-4 py-3 text-sm text-amber-800 dark:text-amber-300"
    }>
      <ShieldAlert size={compact ? 14 : 18} className="mt-0.5 shrink-0" />
      <p>{t("disclaimer")}</p>
    </div>
  );
}
