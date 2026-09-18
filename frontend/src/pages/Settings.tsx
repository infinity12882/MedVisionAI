import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Shield, CreditCard, Code, Gift, Lock } from "lucide-react";
import clsx from "clsx";
import SecurityTab from "./settings/SecurityTab";
import SubscriptionTab from "./settings/SubscriptionTab";
import ApiKeysTab from "./settings/ApiKeysTab";
import ReferralsTab from "./settings/ReferralsTab";
import PrivacyTab from "./settings/PrivacyTab";

type Tab = "security" | "subscription" | "api_keys" | "referrals" | "privacy";

export default function Settings() {
  const { t } = useTranslation();
  const [active, setActive] = useState<Tab>("security");

  const TABS: { key: Tab; icon: typeof Shield; label: string }[] = [
    { key: "security",     icon: Shield,     label: t("settings.tabs.security")     },
    { key: "subscription", icon: CreditCard, label: t("settings.tabs.subscription") },
    { key: "api_keys",     icon: Code,       label: t("settings.tabs.api_keys")     },
    { key: "referrals",    icon: Gift,       label: t("settings.tabs.referrals")    },
    { key: "privacy",      icon: Lock,       label: t("settings.tabs.privacy")      },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("settings.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("settings.subtitle")}</p>
      </div>

      <div className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={clsx(
              "flex shrink-0 items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              active === tab.key
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            )}
          >
            <tab.icon size={15} />
            {tab.label}
          </button>
        ))}
      </div>

      {active === "security"     && <SecurityTab />}
      {active === "subscription" && <SubscriptionTab />}
      {active === "api_keys"     && <ApiKeysTab />}
      {active === "referrals"    && <ReferralsTab />}
      {active === "privacy"      && <PrivacyTab />}
    </div>
  );
}
