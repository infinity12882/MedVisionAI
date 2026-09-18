import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Upload, AlertCircle, ImageIcon } from "lucide-react";
import { diagnosisApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { ImageDiagnosisOut } from "@/types";
import RiskBadge from "@/components/RiskBadge";
import DisclaimerBanner from "@/components/DisclaimerBanner";

const BODY_PARTS = [
  { value: "skin", label: "Skin" },
  { value: "eye", label: "Eye" },
  { value: "tongue", label: "Tongue" },
  { value: "nails", label: "Nails" },
  { value: "throat", label: "Throat" },
  { value: "wound", label: "Wound" },
];

export default function ImageDiagnosis() {
  const [bodyPart, setBodyPart] = useState("skin");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImageDiagnosisOut | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileSelect(selected: File | undefined) {
    if (!selected) return;
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await diagnosisApi.diagnoseImage(file, bodyPart);
      setResult(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Image Diagnosis</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Upload a clear, well-lit photo for AI visual analysis.
        </p>
      </div>

      <DisclaimerBanner compact />

      <div className="card">
        <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">Body part</label>
        <div className="mb-4 grid grid-cols-3 gap-2 sm:grid-cols-6">
          {BODY_PARTS.map((bp) => (
            <button
              key={bp.value}
              onClick={() => setBodyPart(bp.value)}
              className={
                bodyPart === bp.value
                  ? "rounded-lg border-2 border-brand-600 bg-brand-50 px-2 py-2 text-xs font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                  : "rounded-lg border-2 border-slate-200 px-2 py-2 text-xs font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300"
              }
            >
              {bp.label}
            </button>
          ))}
        </div>

        <div
          onClick={() => inputRef.current?.click()}
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 p-8 text-center transition-colors hover:border-brand-400 dark:border-slate-700"
        >
          {preview ? (
            <img src={preview} alt="preview" className="max-h-64 rounded-lg object-contain" />
          ) : (
            <>
              <ImageIcon size={32} className="mb-2 text-slate-400" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Click to upload an image</p>
              <p className="text-xs text-slate-400">JPG, PNG, WEBP — up to 15MB</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files?.[0])}
          />
        </div>

        <button onClick={handleAnalyze} disabled={!file || loading} className="btn-primary mt-4 w-full">
          <Upload size={16} />
          {loading ? "Analyzing..." : "Analyze Image"}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
          {!result.quality_ok ? (
            <div className="flex items-start gap-2 text-amber-700 dark:text-amber-400">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <p className="text-sm">{result.quality_note}</p>
            </div>
          ) : (
            <>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
                  {result.predicted_disease}
                </h2>
                {result.risk_level && <RiskBadge level={result.risk_level} />}
              </div>
              <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">{result.explanation}</p>
              {result.confidence_score != null && (
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Model confidence</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div
                      className="h-full rounded-full bg-brand-600"
                      style={{ width: `${Math.round(result.confidence_score * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-bold text-brand-600">
                    {Math.round(result.confidence_score * 100)}%
                  </span>
                </div>
              )}
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}
