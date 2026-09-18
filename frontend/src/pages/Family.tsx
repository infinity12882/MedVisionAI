import { useEffect, useState } from "react";
import { Plus, Trash2, Users, X } from "lucide-react";
import { familyApi } from "@/api";
import type { FamilyMember } from "@/types";

const RELATIONSHIPS = ["child", "parent", "spouse", "sibling", "other"];

export default function Family() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [showForm, setShowForm] = useState(false);

  function refresh() {
    familyApi.list().then(setMembers).catch(err => {
      alert("Failed to list family members: " + (err?.response?.data?.detail || "Unknown error"));
    });
  }

  useEffect(refresh, []);

  async function handleDelete(id: string) {
    if (!confirm("Remove this family member?")) return;
    try {
      await familyApi.delete(id);
      refresh();
    } catch (err: any) {
      alert("Failed to delete member: " + (err?.response?.data?.detail || "Unknown error"));
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Family Accounts</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage health profiles for children, parents, or anyone in your care.
          </p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          <Plus size={16} /> Add Member
        </button>
      </div>

      {members.length === 0 ? (
        <div className="card flex flex-col items-center gap-3 py-12 text-center text-slate-400">
          <Users size={32} />
          <p className="text-sm">No family members added yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {members.map((m) => (
            <div key={m.id} className="card">
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <h3 className="font-display text-base font-bold text-slate-900 dark:text-white">{m.full_name}</h3>
                  <p className="text-xs capitalize text-slate-500 dark:text-slate-400">{m.relationship}</p>
                </div>
                <button onClick={() => handleDelete(m.id)} className="text-red-400 hover:text-red-600">
                  <Trash2 size={15} />
                </button>
              </div>
              {m.date_of_birth && <p className="text-xs text-slate-500">Born: {m.date_of_birth}</p>}
              {m.chronic_conditions && <p className="mt-1 text-xs text-slate-500">Conditions: {m.chronic_conditions}</p>}
              {m.allergies && <p className="mt-1 text-xs text-slate-500">Allergies: {m.allergies}</p>}
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <AddMemberModal
          onClose={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function AddMemberModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    full_name: "",
    relationship: "child",
    date_of_birth: "",
    sex: "",
    chronic_conditions: "",
    allergies: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await familyApi.create({
        ...form,
        date_of_birth: form.date_of_birth || null,
        sex: form.sex || null,
        chronic_conditions: form.chronic_conditions || null,
        allergies: form.allergies || null,
        notes: form.notes || null,
      });
      onSaved();
    } catch (err: any) {
      alert("Failed to add member: " + (err?.response?.data?.detail || "Unknown error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold text-slate-900 dark:text-white">Add Family Member</h3>
          <button onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <input
            className="input-field"
            placeholder="Full name"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
          <select
            className="input-field"
            value={form.relationship}
            onChange={(e) => setForm({ ...form, relationship: e.target.value })}
          >
            {RELATIONSHIPS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="input-field"
            value={form.date_of_birth}
            onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
          />
          <input
            className="input-field"
            placeholder="Chronic conditions (optional)"
            value={form.chronic_conditions}
            onChange={(e) => setForm({ ...form, chronic_conditions: e.target.value })}
          />
          <input
            className="input-field"
            placeholder="Allergies (optional)"
            value={form.allergies}
            onChange={(e) => setForm({ ...form, allergies: e.target.value })}
          />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving || !form.full_name} className="btn-primary">
            {saving ? "Saving..." : "Add Member"}
          </button>
        </div>
      </div>
    </div>
  );
}
