import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { diseasesApi } from "@/api";
import type { DiseaseListItem } from "@/types";

const SEVERITY_COLOR: Record<string, string> = {
  mild: "badge-low",
  moderate: "badge-moderate",
  severe: "badge-high",
  critical: "badge-emergency",
};

export default function DiseaseLibrary() {
  const [diseases, setDiseases] = useState<DiseaseListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoading(true);
      diseasesApi
        .list(search || undefined)
        .then(setDiseases)
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Disease Library</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Browse the medical knowledge base used to power AI predictions.
        </p>
      </div>

      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9"
          placeholder="Search diseases..."
        />
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">Loading...</p>
      ) : diseases.length === 0 ? (
        <p className="text-sm text-slate-400">No diseases found.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {diseases.map((d) => (
            <Link key={d.id} to={`/diseases/${d.id}`} className="card transition-shadow hover:shadow-md">
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="font-display text-base font-bold text-slate-900 dark:text-white">{d.name}</h3>
                <span className={`badge ${SEVERITY_COLOR[d.severity] ?? "badge-moderate"} shrink-0 capitalize`}>
                  {d.severity}
                </span>
              </div>
              {d.recommended_specialist && (
                <p className="text-xs text-slate-500 dark:text-slate-400">See: {d.recommended_specialist}</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
