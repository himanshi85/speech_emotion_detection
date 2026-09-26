"use client";

import {
  AlertCircle,
  AudioWaveform,
  CheckCircle2,
  Cpu,
  Loader2,
  Mic,
  ShieldCheck,
  Sparkles,
  Upload,
  Waves,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioUploader } from "@/components/AudioUploader";
import { AnalysisReportPanel } from "@/components/AnalysisReportPanel";
import { ModelSelector } from "@/components/ModelSelector";
import { analyzeAudio, checkApiHealth, fetchModels } from "@/lib/api";
import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";
import type { AnalysisReport, InputMode, ModelInfo } from "@/types/analysis";

const FALLBACK_MODELS: ModelInfo[] = [
  {
    key: "mfcc_lstm",
    display_name: "MFCC + LSTM",
    input_type: "mfcc",
    architecture: "MFCC(40) -> LSTM(256x2) -> Linear(8)",
    checkpoint_available: true,
  },
  {
    key: "wav2vec2_xlsr_300m",
    display_name: "Wav2Vec2-XLS-R-300M",
    input_type: "waveform",
    architecture: "XLS-R-300M -> masked pool -> Linear(8)",
    checkpoint_available: false,
  },
];

export function SerStudio() {
  const [inputTab, setInputTab] = useState<InputMode>("upload");
  const [models, setModels] = useState<ModelInfo[]>(FALLBACK_MODELS);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelKey, setModelKey] = useState("mfcc_lstm");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioName, setAudioName] = useState<string>("");
  const [uploaderKey, setUploaderKey] = useState(0);
  const [recorderKey, setRecorderKey] = useState(0);

  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearAudio = useCallback(() => {
    setAudioBlob(null);
    setAudioName("");
    setReport(null);
    setError(null);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setModelsLoading(true);
      const online = await checkApiHealth();
      if (cancelled) return;
      setApiOnline(online);
      if (!online) {
        setModelsLoading(false);
        return;
      }
      try {
        const list = await fetchModels();
        if (cancelled) return;
        setModels(list);
        const firstReady = list.find((m) => m.checkpoint_available)?.key ?? list[0]?.key;
        if (firstReady) setModelKey(firstReady);
      } catch {
        if (!cancelled) setApiOnline(false);
      } finally {
        if (!cancelled) setModelsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedModel = useMemo(
    () => models.find((m) => m.key === modelKey),
    [models, modelKey],
  );

  const canAnalyze = Boolean(audioBlob && selectedModel?.checkpoint_available && !analyzing);

  const runAnalysis = async () => {
    if (!audioBlob || !selectedModel?.checkpoint_available) return;
    setAnalyzing(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyzeAudio(modelKey, audioBlob, audioName || "audio.webm");
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis request failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const switchTab = (tab: InputMode) => {
    setInputTab(tab);
    setUploaderKey((k) => k + 1);
    setRecorderKey((k) => k + 1);
    clearAudio();
  };

  return (
    <div className={ui.page}>
      {/* Top Professional SaaS Navigation */}
      <header className={ui.header}>
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 text-white shadow-[0_4px_12px_rgba(79,70,229,0.25)]">
              <AudioWaveform className="h-5 w-5" strokeWidth={2.2} />
              <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-slate-900">SER Intelligence</span>
                <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700 ring-1 ring-indigo-200">
                  v2.0 SaaS
                </span>
              </div>
              <p className="text-xs text-slate-500">Neural Speech Emotion Recognition Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold shadow-2xs transition-all",
                apiOnline === true && "border-emerald-200 bg-emerald-50 text-emerald-800",
                apiOnline === false && "border-amber-200 bg-amber-50 text-amber-900",
                apiOnline === null && "border-slate-200 bg-slate-50 text-slate-600",
              )}
            >
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  apiOnline === true && "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]",
                  apiOnline === false && "bg-amber-500",
                  apiOnline === null && "animate-pulse bg-slate-400",
                )}
              />
              <span>{apiOnline ? "Inference API Online" : apiOnline === false ? "Local API Offline" : "Connecting..."}</span>
            </div>

            <div className="hidden items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 shadow-2xs sm:flex">
              <ShieldCheck className="h-3.5 w-3.5 text-indigo-600" />
              <span>RAVDESS 8-Class</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main SaaS Workspace Grid */}
      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-12 lg:gap-8">
        {/* Left Column: Audio Control Center */}
        <div className="space-y-6 lg:col-span-7">
          <div className={ui.cardElevated}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className={ui.sectionTitle}>Audio Input Station</h2>
                <p className={ui.sectionDesc}>Select input medium to feed the neural encoder</p>
              </div>

              {audioBlob && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200 animate-in fade-in">
                  <CheckCircle2 className="h-3 w-3" />
                  Audio Loaded
                </span>
              )}
            </div>

            {/* Segmented Mode Tabs */}
            <div className={cn(ui.segmentWrap, "mb-5")}>
              <button
                type="button"
                onClick={() => switchTab("upload")}
                className={cn(
                  "inline-flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all",
                  inputTab === "upload" ? ui.segmentActive : ui.segmentIdle,
                )}
              >
                <Upload className="h-3.5 w-3.5" strokeWidth={2.2} />
                Upload Audio File
              </button>
              <button
                type="button"
                onClick={() => switchTab("record")}
                className={cn(
                  "inline-flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all",
                  inputTab === "record" ? ui.segmentActive : ui.segmentIdle,
                )}
              >
                <Mic className="h-3.5 w-3.5" strokeWidth={2.2} />
                Record Live Speech
              </button>
            </div>

            {/* Tab content */}
            {inputTab === "upload" ? (
              <AudioUploader
                key={uploaderKey}
                disabled={analyzing}
                onClear={clearAudio}
                onFileReady={(file) => {
                  setAudioBlob(file);
                  setAudioName(file.name);
                  setReport(null);
                  setError(null);
                }}
              />
            ) : (
              <AudioRecorder
                key={recorderKey}
                disabled={analyzing}
                onClear={clearAudio}
                onRecordingReady={(blob, name) => {
                  setAudioBlob(blob);
                  setAudioName(name);
                  setReport(null);
                  setError(null);
                }}
              />
            )}

            {/* Model Selector Card & Trigger */}
            <div className="mt-6 border-t border-slate-100 pt-5">
              <ModelSelector
                models={models}
                value={modelKey}
                onChange={setModelKey}
                loading={modelsLoading}
              />
            </div>

            {/* Primary Action Button */}
            <div className="mt-6">
              <button
                type="button"
                disabled={!canAnalyze || apiOnline === false}
                onClick={runAnalysis}
                className={cn(ui.btnPrimary, "w-full py-4 text-base font-bold")}
              >
                {analyzing ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin text-white" />
                    <span>Processing Neural Inference...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 text-amber-300" />
                    <span>Run Neural Emotion Analysis</span>
                  </>
                )}
              </button>

              {!audioBlob && (
                <p className="mt-2.5 text-center text-xs font-medium text-slate-400">
                  Provide an audio sample above to unlock neural analysis
                </p>
              )}
            </div>

            {error && (
              <div className={cn(ui.alertError, "mt-4 flex gap-2.5")}>
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
                <div>
                  <p className="font-bold text-rose-900">Inference Error</p>
                  <p className="mt-0.5 text-xs text-rose-800">{error}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Interactive Diagnostic Report */}
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-20">
            <AnalysisReportPanel report={report} loading={analyzing} />
          </div>
        </div>
      </main>

      {/* Clean Professional Footer */}
      <footer className="border-t border-slate-200/80 bg-white/70 py-6 text-center text-xs text-slate-500 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 sm:flex-row sm:px-6">
          <p>© 2026 SER Intelligence Studio · RAVDESS Emotion Classifier</p>
          <div className="flex items-center gap-3 text-slate-400">
            <span>Actor-Independent Split</span>
            <span>•</span>
            <span>16 kHz Mono</span>
            <span>•</span>
            <span>Macro-F1 Benchmark</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
