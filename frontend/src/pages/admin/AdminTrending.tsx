import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { adminApi } from "@/api";
import type { TrendingCondition } from "@/types";
import RiskBadge from "@/components/RiskBadge";

export default function AdminTrending() {
  const { t } = useTranslation();
  const [data, setData] = useState<TrendingCondition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.trendingConditions().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("admin.trending.title")}</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("admin.trending.subtitle")}</p>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">{t("common.loading")}</p>
      ) : data.length === 0 ? (
        <p className="text-sm text-slate-400">{t("admin.trending.no_data")}</p>
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-xs uppercase text-slate-400 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">{t("admin.trending.disease")}</th>
                <th className="px-4 py-3">{t("admin.trending.cases")}</th>
                <th className="px-4 py-3">{t("admin.trending.risk")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {data.map((row, idx) => (
                <tr key={row.disease_name} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="px-4 py-2.5 text-slate-400">#{idx + 1}</td>
                  <td className="px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200">{row.disease_name}</td>
                  <td className="px-4 py-2.5">
                    <span className="rounded-full bg-brand-100 px-2.5 py-0.5 text-xs font-bold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                      {row.case_count}
                    </span>
                  </td>
                  <td className="px-4 py-2.5"><RiskBadge level={row.risk_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
