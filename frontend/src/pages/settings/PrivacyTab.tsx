import { useState } from "react";
import { Download, Trash2, AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { privacyApi } from "@/api";
import { useAppDispatch } from "@/hooks/redux";
import { logout } from "@/store/slices/authSlice";
import { useNavigate } from "react-router-dom";
import { apiClient } from "@/api/client";

export default function PrivacyTab() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (!password.trim()) return;
    setDeleting(true); setError(null);
    try {
      await apiClient.post("/privacy/delete-account", null, { params: { password } });
      dispatch(logout());
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Incorrect password");
    } finally { setDeleting(false); }
  }

  return (
    <div className="space-y-6">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("settings.privacy.title")}</h2>

      {/* Export */}
      <div className="card">
        <div className="mb-3 flex items-start gap-3">
          <Download size={20} className="mt-0.5 shrink-0 text-brand-600" />
          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">{t("settings.privacy.export_title")}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">{t("settings.privacy.export_subtitle")}</p>
          </div>
        </div>
        <button onClick={() => privacyApi.exportData()} className="btn-secondary text-sm">
          <Download size={14} />{t("settings.privacy.export_btn")}
        </button>
      </div>

      {/* Delete */}
      <div className="card border-red-200 dark:border-red-900">
        <div className="mb-3 flex items-start gap-3">
          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-700 dark:text-red-400">{t("settings.privacy.delete_title")}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">{t("settings.privacy.delete_subtitle")}</p>
          </div>
        </div>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="rounded-xl border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800"
          >
            <Trash2 size={14} className="inline mr-1" />
            {t("settings.privacy.delete_btn")}
          </button>
        ) : (
          <div className="space-y-3">
            <p className="text-sm font-medium text-red-700 dark:text-red-400">{t("settings.privacy.delete_confirm")}</p>
            <input
              type="password"
              className="input-field"
              placeholder={t("settings.privacy.password_placeholder")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {error && <p className="text-xs text-red-600">{error}</p>}
            <div className="flex gap-2">
              <button onClick={() => setShowDeleteConfirm(false)} className="btn-secondary flex-1">{t("common.cancel")}</button>
              <button
                onClick={handleDelete}
                disabled={deleting || !password}
                className="flex-1 rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? t("common.loading") : t("settings.privacy.delete_btn")}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
