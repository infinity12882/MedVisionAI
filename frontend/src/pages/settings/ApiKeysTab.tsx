import { useEffect, useState } from "react";
import { Plus, Trash2, Copy, Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { apiKeysApi } from "@/api";
import type { ApiKeyItem } from "@/types";

export default function ApiKeysTab() {
  const { t } = useTranslation();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function refresh() { apiKeysApi.list().then(setKeys).catch(() => {}); }
  useEffect(refresh, []);

  async function handleCreate() {
    if (!name.trim()) return;
    const created = await apiKeysApi.create(name);
    setNewKey(created.full_key);
    setName("");
    refresh();
  }

  function handleCopy(key: string) {
    navigator.clipboard.writeText(key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleRevoke(id: string) {
    if (!confirm("Revoke this API key?")) return;
    await apiKeysApi.revoke(id);
    refresh();
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("settings.api_keys.title")}</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">{t("settings.api_keys.subtitle")}</p>
      </div>

      {newKey && (
        <div className="card border-brand-300 dark:border-brand-700 space-y-2">
          <p className="text-xs font-semibold text-emerald-600">{t("settings.api_keys.key_revealed")}</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 rounded-lg bg-slate-50 px-3 py-2 text-xs font-mono break-all text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {newKey}
            </code>
            <button onClick={() => handleCopy(newKey)} className="btn-secondary text-xs">
              {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
            </button>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <input
          className="input-field flex-1"
          placeholder={t("settings.api_keys.name_placeholder")}
          value={name} onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
        <button onClick={handleCreate} disabled={!name.trim()} className="btn-primary">
          <Plus size={14} />{t("settings.api_keys.create_btn")}
        </button>
      </div>

      {keys.length === 0 ? (
        <p className="text-sm text-slate-400">{t("settings.api_keys.no_keys")}</p>
      ) : (
        <div className="space-y-3">
          {keys.map((k) => (
            <div key={k.id} className="card flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="font-medium text-slate-800 dark:text-slate-200">{k.name}</p>
                <p className="font-mono text-xs text-slate-500">{k.key_prefix}••••••••</p>
                <p className="text-xs text-slate-400">
                  {k.total_requests} {t("settings.api_keys.requests")} ·{" "}
                  {k.last_used_at
                    ? `${t("settings.api_keys.last_used")} ${new Date(k.last_used_at).toLocaleDateString()}`
                    : t("settings.api_keys.never")}
                </p>
              </div>
              <button onClick={() => handleRevoke(k.id)} className="shrink-0 text-red-400 hover:text-red-600">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
