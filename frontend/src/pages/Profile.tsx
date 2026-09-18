import { useEffect, useState } from "react";
import { usersApi } from "@/api";
import type { PatientProfile } from "@/types";
import { useAppSelector } from "@/hooks/redux";

export default function Profile() {
  const { user } = useAppSelector((s) => s.auth);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "patient") {
      usersApi.getPatientProfile().then(setProfile);
    }
  }, [user]);

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await usersApi.updatePatientProfile(profile);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  if (user?.role !== "patient") {
    return <p className="text-sm text-slate-500">Profile editing is available for patient accounts.</p>;
  }

  if (!profile) return <p className="text-sm text-slate-400">Loading...</p>;

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">My Profile</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          This information powers your AI Health Score and personalizes recommendations.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="card grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Height (cm)">
          <input
            type="number"
            className="input-field"
            value={profile.height_cm ?? ""}
            onChange={(e) => setProfile({ ...profile, height_cm: e.target.value ? Number(e.target.value) : null })}
          />
        </Field>
        <Field label="Weight (kg)">
          <input
            type="number"
            className="input-field"
            value={profile.weight_kg ?? ""}
            onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value ? Number(e.target.value) : null })}
          />
        </Field>
        <Field label="Average sleep (hours/night)">
          <input
            type="number"
            step="0.5"
            className="input-field"
            value={profile.sleep_hours_avg ?? ""}
            onChange={(e) =>
              setProfile({ ...profile, sleep_hours_avg: e.target.value ? Number(e.target.value) : null })
            }
          />
        </Field>
        <Field label="Water intake (liters/day)">
          <input
            type="number"
            step="0.1"
            className="input-field"
            value={profile.water_intake_liters_avg ?? ""}
            onChange={(e) =>
              setProfile({ ...profile, water_intake_liters_avg: e.target.value ? Number(e.target.value) : null })
            }
          />
        </Field>
        <Field label="Exercise (minutes/week)">
          <input
            type="number"
            className="input-field"
            value={profile.exercise_minutes_per_week ?? ""}
            onChange={(e) =>
              setProfile({ ...profile, exercise_minutes_per_week: e.target.value ? Number(e.target.value) : null })
            }
          />
        </Field>
        <Field label="Stress level (1-10)">
          <input
            type="number"
            min={1}
            max={10}
            className="input-field"
            value={profile.stress_level ?? ""}
            onChange={(e) => setProfile({ ...profile, stress_level: e.target.value ? Number(e.target.value) : null })}
          />
        </Field>
        <Field label="Chronic conditions">
          <input
            className="input-field"
            value={profile.chronic_conditions ?? ""}
            onChange={(e) => setProfile({ ...profile, chronic_conditions: e.target.value })}
            placeholder="e.g. asthma, diabetes"
          />
        </Field>
        <Field label="Allergies">
          <input
            className="input-field"
            value={profile.allergies ?? ""}
            onChange={(e) => setProfile({ ...profile, allergies: e.target.value })}
            placeholder="e.g. penicillin"
          />
        </Field>
      </div>

      <button onClick={handleSave} disabled={saving} className="btn-primary">
        {saving ? "Saving..." : saved ? "Saved ✓" : "Save changes"}
      </button>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">{label}</label>
      {children}
    </div>
  );
}
