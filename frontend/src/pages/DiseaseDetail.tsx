import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { diseasesApi } from "@/api";
import type { Disease } from "@/types";
import DisclaimerBanner from "@/components/DisclaimerBanner";

const FIELDS: { key: keyof Disease; label: string }[] = [
  { key: "description", label: "Description" },
  { key: "causes", label: "Causes" },
  { key: "risk_factors", label: "Risk Factors" },
  { key: "complications", label: "Complications" },
  { key: "treatment_overview", label: "Treatment Overview" },
  { key: "prevention", label: "Prevention" },
  { key: "nutrition_advice", label: "Nutrition Advice" },
  { key: "foods_to_eat", label: "Foods to Eat" },
  { key: "foods_to_avoid", label: "Foods to Avoid" },
  { key: "lifestyle_advice", label: "Lifestyle Advice" },
  { key: "emergency_warning_signs", label: "Emergency Warning Signs" },
];

export default function DiseaseDetail() {
  const { id } = useParams<{ id: string }>();
  const [disease, setDisease] = useState<Disease | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (id) {
      diseasesApi.get(id)
        .then(setDisease)
        .catch(() => setError(true));
    }
  }, [id]);

  if (error) return <p className="text-sm text-red-500">Failed to load disease details.</p>;
  if (!disease) return <p className="text-sm text-slate-400">Loading...</p>;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link to="/diseases" className="flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600">
        <ArrowLeft size={14} /> Back to library
      </Link>

      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white">{disease.name}</h1>
        {disease.recommended_specialist && (
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Recommended specialist: <span className="font-medium">{disease.recommended_specialist}</span>
          </p>
        )}
      </div>

      <DisclaimerBanner compact />

      {FIELDS.map(
        (field) =>
          disease[field.key] && (
            <div key={field.key} className="card">
              <h2 className="mb-2 font-display text-base font-bold text-slate-900 dark:text-white">{field.label}</h2>
              <p className="whitespace-pre-line text-sm text-slate-600 dark:text-slate-300">
                {disease[field.key] as string}
              </p>
            </div>
          )
      )}

      {disease.symptom_links.length > 0 && (
        <div className="card">
          <h2 className="mb-3 font-display text-base font-bold text-slate-900 dark:text-white">Common Symptoms</h2>
          <div className="flex flex-wrap gap-2">
            {[...disease.symptom_links]
              .sort((a, b) => b.importance_score - a.importance_score)
              .map((link) => (
                <span
                  key={link.symptom_id}
                  className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                >
                  {link.symptom.name}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
