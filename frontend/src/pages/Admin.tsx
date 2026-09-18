import { useState } from "react";
import { useTranslation } from "react-i18next";
import AdminOverview from "./admin/AdminOverview";
import AdminDiseases from "./admin/AdminDiseases";
import AdminSymptoms from "./admin/AdminSymptoms";
import AdminMedications from "./admin/AdminMedications";
import AdminUsers from "./admin/AdminUsers";
import AdminSystem from "./admin/AdminSystem";
import AdminTrending from "./admin/AdminTrending";

type Tab = "overview"|"diseases"|"symptoms"|"medications"|"users"|"system"|"trends";

export default function Admin() {
  const { t } = useTranslation();
  const [active, setActive] = useState<Tab>("overview");

  const TABS: { key: Tab; label: string }[] = [
    { key: "overview",     label: t("admin.tabs.overview")     },
    { key: "diseases",     label: t("admin.tabs.diseases")     },
    { key: "symptoms",     label: t("admin.tabs.symptoms")     },
    { key: "medications",  label: t("admin.tabs.medications")  },
    { key: "users",        label: t("admin.tabs.users")        },
    { key: "system",       label: t("admin.tabs.system")       },
    { key: "trends",       label: t("admin.tabs.trends")       },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("admin.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("admin.subtitle")}</p>
      </div>
      <div className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800">
        {TABS.map((tab) => (
          <button key={tab.key} onClick={() => setActive(tab.key)}
            className={active === tab.key
              ? "shrink-0 border-b-2 border-brand-600 px-4 py-2.5 text-sm font-semibold text-brand-600"
              : "shrink-0 border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }
          >{tab.label}</button>
        ))}
      </div>
      {active === "overview"    && <AdminOverview />}
      {active === "diseases"    && <AdminDiseases />}
      {active === "symptoms"    && <AdminSymptoms />}
      {active === "medications" && <AdminMedications />}
      {active === "users"       && <AdminUsers />}
      {active === "system"      && <AdminSystem />}
      {active === "trends"      && <AdminTrending />}
    </div>
  );
}
