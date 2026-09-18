import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { adminApi } from "@/api";
import type { User } from "@/types";

export default function AdminUsers() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);

  function refresh() { adminApi.listUsers().then(setUsers); }
  useEffect(refresh, []);

  async function toggleActive(user: User) {
    if (user.is_active) await adminApi.deactivateUser(user.id);
    else await adminApi.activateUser(user.id);
    refresh();
  }

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("admin.tabs.users")} ({users.length})</h2>
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase text-slate-400 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">{t("auth.full_name")}</th>
              <th className="px-4 py-3">{t("auth.email")}</th>
              <th className="px-4 py-3">{t("common.role")}</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200">{u.full_name}</td>
                <td className="px-4 py-2.5 text-slate-500">{u.email}</td>
                <td className="px-4 py-2.5 capitalize text-slate-500">{u.role}</td>
                <td className="px-4 py-2.5">
                  <span className={u.is_active ? "badge badge-low" : "badge badge-emergency"}>
                    {u.is_active ? t("common.active") : t("common.deactivated")}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => toggleActive(u)} className="text-xs font-semibold text-brand-600 hover:underline">
                    {u.is_active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
