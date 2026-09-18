import { useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { diseasesApi, symptomsApi } from "@/api";
import type { Disease, DiseaseListItem, Symptom } from "@/types";

const SEVERITIES = ["mild", "moderate", "severe", "critical"];

export default function AdminDiseases() {
  const [diseases, setDiseases] = useState<DiseaseListItem[]>([]);
  const [symptoms, setSymptoms] = useState<Symptom[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [selected, setSelected] = useState<Disease | null>(null);

  function refresh() {
    diseasesApi.list().then(setDiseases);
  }

  useEffect(() => {
    refresh();
    symptomsApi.list().then(setSymptoms);
  }, []);

  async function handleDelete(id: string) {
    if (!confirm("Delete this disease? This cannot be undone.")) return;
    await diseasesApi.delete(id);
    refresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">Diseases ({diseases.length})</h2>
        <button onClick={() => setShowForm(true)} className="btn-primary text-sm">
          <Plus size={14} /> Add Disease
        </button>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase text-slate-400 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Specialist</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {diseases.map((d) => (
              <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td
                  className="cursor-pointer px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200"
                  onClick={() => diseasesApi.get(d.id).then(setSelected)}
                >
                  {d.name}
                </td>
                <td className="px-4 py-2.5 capitalize text-slate-500">{d.severity}</td>
                <td className="px-4 py-2.5 text-slate-500">{d.recommended_specialist ?? "—"}</td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => handleDelete(d.id)} className="text-red-500 hover:text-red-700">
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(showForm || selected) && (
        <DiseaseFormModal
          symptoms={symptoms}
          disease={selected}
          onClose={() => {
            setShowForm(false);
            setSelected(null);
          }}
          onSaved={() => {
            setShowForm(false);
            setSelected(null);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function DiseaseFormModal({
  symptoms,
  disease,
  onClose,
  onSaved,
}: {
  symptoms: Symptom[];
  disease: Disease | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
    name: disease?.name ?? "",
    severity: disease?.severity ?? "moderate",
    recommended_specialist: disease?.recommended_specialist ?? "",
    avg_recovery_days: disease?.avg_recovery_days ?? undefined,
    description: disease?.description ?? "",
    causes: disease?.causes ?? "",
    lifestyle_advice: disease?.lifestyle_advice ?? "",
    foods_to_eat: disease?.foods_to_eat ?? "",
    foods_to_avoid: disease?.foods_to_avoid ?? "",
    emergency_warning_signs: disease?.emergency_warning_signs ?? "",
  });
  const [symptomLinks, setSymptomLinks] = useState<{ symptom_id: string; importance_score: number }[]>(
    disease?.symptom_links.map((l) => ({ symptom_id: l.symptom_id, importance_score: l.importance_score })) ?? []
  );
  const [saving, setSaving] = useState(false);

  function toggleSymptom(symptomId: string) {
    setSymptomLinks((prev) =>
      prev.some((l) => l.symptom_id === symptomId)
        ? prev.filter((l) => l.symptom_id !== symptomId)
        : [...prev, { symptom_id: symptomId, importance_score: 0.7 }]
    );
  }

  async function handleSave() {
    setSaving(true);
    try {
      const payload = { ...form, symptoms: symptomLinks };
      if (disease) {
        await diseasesApi.update(disease.id, payload);
      } else {
        await diseasesApi.create(payload);
      }
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold text-slate-900 dark:text-white">
            {disease ? "Edit Disease" : "Add Disease"}
          </h3>
          <button onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <input
            className="input-field"
            placeholder="Disease name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <select
              className="input-field"
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <input
              className="input-field"
              placeholder="Recommended specialist"
              value={form.recommended_specialist}
              onChange={(e) => setForm({ ...form, recommended_specialist: e.target.value })}
            />
          </div>
          <textarea
            className="input-field"
            placeholder="Description"
            rows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <textarea
            className="input-field"
            placeholder="Causes"
            rows={2}
            value={form.causes}
            onChange={(e) => setForm({ ...form, causes: e.target.value })}
          />
          <textarea
            className="input-field"
            placeholder="Lifestyle advice / home care"
            rows={2}
            value={form.lifestyle_advice}
            onChange={(e) => setForm({ ...form, lifestyle_advice: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              className="input-field"
              placeholder="Foods to eat"
              value={form.foods_to_eat}
              onChange={(e) => setForm({ ...form, foods_to_eat: e.target.value })}
            />
            <input
              className="input-field"
              placeholder="Foods to avoid"
              value={form.foods_to_avoid}
              onChange={(e) => setForm({ ...form, foods_to_avoid: e.target.value })}
            />
          </div>
          <textarea
            className="input-field"
            placeholder="Emergency warning signs"
            rows={2}
            value={form.emergency_warning_signs}
            onChange={(e) => setForm({ ...form, emergency_warning_signs: e.target.value })}
          />

          <div>
            <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">Linked symptoms</p>
            <div className="flex max-h-40 flex-wrap gap-2 overflow-y-auto">
              {symptoms.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => toggleSymptom(s.id)}
                  className={
                    symptomLinks.some((l) => l.symptom_id === s.id)
                      ? "rounded-full bg-brand-600 px-3 py-1 text-xs font-medium text-white"
                      : "rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                  }
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving || !form.name} className="btn-primary">
            {saving ? "Saving..." : "Save Disease"}
          </button>
        </div>
      </div>
    </div>
  );
}
