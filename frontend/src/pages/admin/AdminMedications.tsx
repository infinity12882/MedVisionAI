import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { medicationsApi } from "@/api";
import type { Medication } from "@/types";

export default function AdminMedications() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [form, setForm] = useState({ name: "", drug_category: "", linked_disease_tags: "" });

  function refresh() {
    medicationsApi.list().then(setMedications);
  }

  useEffect(refresh, []);

  async function handleCreate() {
    if (!form.name.trim()) return;
    await medicationsApi.create(form);
    setForm({ name: "", drug_category: "", linked_disease_tags: "" });
    refresh();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this medication?")) return;
    await medicationsApi.delete(id);
    refresh();
  }

  return (
    <div className="space-y-4">
      <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
        Medications ({medications.length})
      </h2>

      <div className="card grid grid-cols-1 gap-2 sm:grid-cols-4">
        <input
          className="input-field"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="input-field"
          placeholder="Category"
          value={form.drug_category}
          onChange={(e) => setForm({ ...form, drug_category: e.target.value })}
        />
        <input
          className="input-field"
          placeholder="Linked diseases (comma sep.)"
          value={form.linked_disease_tags}
          onChange={(e) => setForm({ ...form, linked_disease_tags: e.target.value })}
        />
        <button onClick={handleCreate} className="btn-primary">
          <Plus size={14} /> Add
        </button>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase text-slate-400 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Linked Diseases</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {medications.map((m) => (
              <tr key={m.id}>
                <td className="px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200">{m.name}</td>
                <td className="px-4 py-2.5 text-slate-500">{m.drug_category ?? "—"}</td>
                <td className="px-4 py-2.5 text-slate-500">{m.linked_disease_tags ?? "—"}</td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => handleDelete(m.id)} className="text-red-500 hover:text-red-700">
                    <Trash2 size={15} />
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
