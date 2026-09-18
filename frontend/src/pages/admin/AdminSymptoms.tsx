import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { symptomsApi } from "@/api";
import type { Symptom } from "@/types";

export default function AdminSymptoms() {
  const [symptoms, setSymptoms] = useState<Symptom[]>([]);
  const [name, setName] = useState("");
  const [bodySystem, setBodySystem] = useState("");

  function refresh() {
    symptomsApi.list().then(setSymptoms);
  }

  useEffect(refresh, []);

  async function handleCreate() {
    if (!name.trim()) return;
    await symptomsApi.create({ name, body_system: bodySystem || undefined });
    setName("");
    setBodySystem("");
    refresh();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this symptom?")) return;
    await symptomsApi.delete(id);
    refresh();
  }

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">Symptoms ({symptoms.length})</h2>

      <div className="card flex flex-wrap gap-2">
        <input
          className="input-field flex-1 min-w-[180px]"
          placeholder="Symptom name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="input-field flex-1 min-w-[180px]"
          placeholder="Body system (optional)"
          value={bodySystem}
          onChange={(e) => setBodySystem(e.target.value)}
        />
        <button onClick={handleCreate} className="btn-primary">
          <Plus size={14} /> Add
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {symptoms.map((s) => (
          <span
            key={s.id}
            className="flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm dark:bg-slate-800 dark:text-slate-200"
          >
            {s.name}
            {s.body_system && <span className="text-slate-400">· {s.body_system}</span>}
            <button onClick={() => handleDelete(s.id)} className="text-red-400 hover:text-red-600">
              <Trash2 size={12} />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
