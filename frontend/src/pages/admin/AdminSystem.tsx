import { useEffect, useState } from "react";
import { RefreshCw, Brain } from "lucide-react";
import { useTranslation } from "react-i18next";
import { adminApi } from "@/api";

interface AuditRow { id:string; user_id:string|null; action:string; resource_type:string|null; resource_id:string|null; ip_address:string|null; created_at:string; }

export default function AdminSystem() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<AuditRow[]>([]);
  const [msg, setMsg] = useState<{key:"rag"|"train"; text:string}|null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { adminApi.auditLogs().then(setLogs); }, []);

  async function handle(action: "rag"|"train") {
    setBusy(true); setMsg(null);
    try {
      const res = action === "rag" ? await adminApi.reindexKnowledgeBase() : await adminApi.retrainVisionModel();
      setMsg({ key: action, text: res.detail });
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="card">
          <h3 className="mb-1 font-display text-base font-bold text-slate-900 dark:text-white">{t("admin.rag.title")}</h3>
          <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">{t("admin.rag.subtitle")}</p>
          <button onClick={() => handle("rag")} disabled={busy} className="btn-secondary text-sm">
            <RefreshCw size={14} /> {t("admin.rag.rebuild_btn")}
          </button>
          {msg?.key === "rag" && <p className="mt-2 text-xs text-emerald-600">{msg.text}</p>}
        </div>
        <div className="card">
          <h3 className="mb-1 font-display text-base font-bold text-slate-900 dark:text-white">{t("admin.vision.title")}</h3>
          <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">{t("admin.vision.subtitle")}</p>
          <button onClick={() => handle("train")} disabled={busy} className="btn-secondary text-sm">
            <Brain size={14} /> {t("admin.vision.retrain_btn")}
          </button>
          {msg?.key === "train" && <p className="mt-2 text-xs text-emerald-600">{msg.text}</p>}
        </div>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase text-slate-400 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Resource</th>
              <th className="px-4 py-3">IP</th>
              <th className="px-4 py-3">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="px-4 py-2.5 font-mono text-xs text-slate-700 dark:text-slate-300">{log.action}</td>
                <td className="px-4 py-2.5 text-xs text-slate-500">{log.resource_type ?? "—"} {log.resource_id ? `#${log.resource_id.slice(0,8)}` : ""}</td>
                <td className="px-4 py-2.5 text-xs text-slate-500">{log.ip_address ?? "—"}</td>
                <td className="px-4 py-2.5 text-xs text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
