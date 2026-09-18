import { AlertTriangle, AlertCircle, CheckCircle2, Siren } from "lucide-react";
import { useTranslation } from "react-i18next";
import clsx from "clsx";

const CONFIG: Record<string, { key: string; icon: typeof CheckCircle2; className: string }> = {
  low:       { key: "risk.low",       icon: CheckCircle2, className: "badge-low"       },
  moderate:  { key: "risk.moderate",  icon: AlertCircle,  className: "badge-moderate"  },
  high:      { key: "risk.high",      icon: AlertTriangle,className: "badge-high"      },
  emergency: { key: "risk.emergency", icon: Siren,        className: "badge-emergency" },
};

export default function RiskBadge({ level }: { level: string }) {
  const { t } = useTranslation();
  const config = CONFIG[level] ?? CONFIG.moderate;
  const Icon = config.icon;
  return (
    <span className={clsx("badge", config.className)}>
      <Icon size={13} />
      {t(config.key)}
    </span>
  );
}
