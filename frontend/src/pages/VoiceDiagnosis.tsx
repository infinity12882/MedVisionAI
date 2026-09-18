import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Mic, Square, Upload, AlertCircle } from "lucide-react";
import { diagnosisApi, historyApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { VoiceDiagnosisOut } from "@/types";
import RiskBadge from "@/components/RiskBadge";
import DisclaimerBanner from "@/components/DisclaimerBanner";

export default function VoiceDiagnosis() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VoiceDiagnosisOut | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function startRecording() {
    setError(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch {
      setError("Microphone access was denied or is unavailable. You can upload an audio file instead.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  function handleFileUpload(file: File | undefined) {
    if (!file) return;
    setAudioBlob(file);
    setAudioUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (!audioBlob) return;
    setLoading(true);
    setError(null);
    try {
      const data = await diagnosisApi.diagnoseVoice(audioBlob);
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
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Voice Diagnosis</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Speak your symptoms out loud, or upload a voice recording.
        </p>
      </div>

      <DisclaimerBanner compact />

      <div className="card flex flex-col items-center gap-4 py-10">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={
            isRecording
              ? "flex h-20 w-20 items-center justify-center rounded-full bg-red-500 text-white shadow-lg shadow-red-500/30 transition-transform active:scale-95"
              : "flex h-20 w-20 items-center justify-center rounded-full bg-brand-600 text-white shadow-lg shadow-brand-600/30 transition-transform active:scale-95"
          }
        >
          {isRecording ? <Square size={28} /> : <Mic size={28} />}
        </button>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
          {isRecording ? "Recording... tap to stop" : "Tap to start recording"}
        </p>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="h-px w-12 bg-slate-200 dark:bg-slate-700" />
          or
          <span className="h-px w-12 bg-slate-200 dark:bg-slate-700" />
        </div>

        <button onClick={() => fileInputRef.current?.click()} className="btn-secondary text-sm">
          <Upload size={14} />
          Upload audio file
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={(e) => handleFileUpload(e.target.files?.[0])}
        />

        {audioUrl && (
          <div className="w-full">
            <audio src={audioUrl} controls className="w-full" />
            <button onClick={handleAnalyze} disabled={loading} className="btn-primary mt-3 w-full">
              {loading ? "Transcribing & analyzing..." : "Analyze Recording"}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="card">
            <h2 className="mb-2 font-display text-base font-bold text-slate-900 dark:text-white">Transcript</h2>
            <p className="text-sm italic text-slate-600 dark:text-slate-300">"{result.transcript || "(empty)"}"</p>
            {result.extracted_symptoms.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.extracted_symptoms.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>

          {result.prediction ? (
            <div className="card">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
                  {result.prediction.top_disease}
                </h2>
                <RiskBadge level={result.prediction.risk_level} />
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300">{result.prediction.results[0]?.explanation}</p>
              <button
                onClick={() => result.prediction && historyApi.downloadPdf(result.prediction.id)}
                className="btn-secondary mt-4"
              >
                Download PDF Report
              </button>
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No clear symptoms were recognized in this recording. Try the text symptom checker instead.
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
}
