import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Pill, BookOpen, Syringe, Watch } from "lucide-react";
import clsx from "clsx";
import MedicationsTab from "./health/MedicationsTab";
import DiaryTab from "./health/DiaryTab";
import VaccinationsTab from "./health/VaccinationsTab";
import WearablesTab from "./health/WearablesTab";

type Tab = "medications" | "diary" | "vaccinations" | "wearables";

export default function HealthTracking() {
  const { t } = useTranslation();
  const [active, setActive] = useState<Tab>("medications");

  const TABS: { key: Tab; icon: typeof Pill; label: string }[] = [
    { key: "medications",  icon: Pill,     label: t("health_tracking.tabs.medications")  },
    { key: "diary",        icon: BookOpen, label: t("health_tracking.tabs.diary")         },
    { key: "vaccinations", icon: Syringe,  label: t("health_tracking.tabs.vaccinations")  },
    { key: "wearables",    icon: Watch,    label: t("health_tracking.tabs.wearables")      },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">
          {t("health_tracking.title")}
        </h1>
      </div>

      {/* Tab bar */}
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

      {active === "medications"  && <MedicationsTab />}
      {active === "diary"        && <DiaryTab />}
      {active === "vaccinations" && <VaccinationsTab />}
      {active === "wearables"    && <WearablesTab />}
    </div>
  );
}
