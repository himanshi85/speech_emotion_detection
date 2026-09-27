"use client";

import {
  AlertCircle,
  AudioWaveform,
  CheckCircle2,
  Loader2,
  Mic,
  RefreshCw,
  Upload,
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
    key: "hindi_mfcc_cnn_bilstm",
    display_name: "Hindi Emotion Specialist (MFCC + CNN-BiLSTM)",
    input_type: "mfcc",
    architecture: "MFCC(40) -> CNN-BiLSTM(256x2) -> Linear(5)",
    checkpoint_available: true,
  },
  {
    key: "wav2vec2_xlsr_300m",
    display_name: "Wav2Vec2-XLS-R-300M",
    input_type: "waveform",
    architecture: "XLS-R-300M -> Masked Avg Pool -> Linear(8)",
    checkpoint_available: false,
  },
];

export function SerStudio() {
  const [inputTab, setInputTab] = useState<InputMode>("upload");
  const [models, setModels] = useState<ModelInfo[]>(FALLBACK_MODELS);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelKey, setModelKey] = useState("hindi_mfcc_cnn_bilstm");
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

  const refreshSystem = useCallback(async () => {
    setModelsLoading(true);
    const online = await checkApiHealth();
    setApiOnline(online);
    if (!online) {
      setModelsLoading(false);
      return;
    }
    try {
      const list = await fetchModels();
      setModels(list);
      const firstReady = list.find((m) => m.checkpoint_available)?.key ?? list[0]?.key;
      if (firstReady) setModelKey(firstReady);
    } catch {
      setApiOnline(false);
    } finally {
      setModelsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSystem();
  }, [refreshSystem]);

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
      const result = await analyzeAudio(modelKey, audioBlob, audioName || "audio.wav");
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Emotion analysis request failed.");
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
      {/* Clean Minimal White Header */}
      <header className={ui.header}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white shadow-2xs">
              <AudioWaveform className="h-4 w-4" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight text-slate-900">
                Speech Emotion Recognition
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Status indicator */}
            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 shadow-2xs">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  apiOnline === true && "bg-emerald-500",
                  apiOnline === false && "bg-amber-500",
                  apiOnline === null && "bg-slate-300 animate-pulse",
                )}
              />
              <span>{apiOnline ? "Server Online" : apiOnline === false ? "Server Offline" : "Connecting..."}</span>
            </div>

            <button
              type="button"
              onClick={refreshSystem}
              title="Refresh connection"
              className="text-slate-400 hover:text-slate-700 transition-colors p-1"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", modelsLoading && "animate-spin")} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Studio Container */}
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:gap-8 items-start">
          {/* Left Column: Input Station & Controls (6 cols) */}
          <div className="space-y-6 lg:col-span-6">
            <div className={ui.card}>
              <div className="mb-4">
                <h2 className={ui.sectionTitle}>Audio Input</h2>
                <p className={ui.sectionDesc}>
                  Upload an audio file or record speech directly with your microphone.
                </p>
              </div>

              {/* Segmented Mode Switcher */}
              <div className={cn(ui.segmentWrap, "mb-4")}>
                <button
                  type="button"
                  onClick={() => switchTab("upload")}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-1.5 py-2 text-xs font-medium transition-all",
                    inputTab === "upload" ? ui.segmentActive : ui.segmentIdle,
                  )}
                >
                  <Upload className="h-3.5 w-3.5" />
                  <span>Upload Audio</span>
                </button>
                <button
                  type="button"
                  onClick={() => switchTab("record")}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-1.5 py-2 text-xs font-medium transition-all",
                    inputTab === "record" ? ui.segmentActive : ui.segmentIdle,
                  )}
                >
                  <Mic className="h-3.5 w-3.5" />
                  <span>Record Voice</span>
                </button>
              </div>

              {/* Ingestion Content */}
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

              {/* Model Selection */}
              <div className="mt-5 pt-4 border-t border-slate-100">
                <ModelSelector
                  models={models}
                  value={modelKey}
                  onChange={setModelKey}
                  loading={modelsLoading}
                />
              </div>

              {/* Analyze Action */}
              <div className="mt-5">
                <button
                  type="button"
                  disabled={!canAnalyze || apiOnline === false}
                  onClick={runAnalysis}
                  className={cn(ui.btnPrimary, "w-full py-3 text-xs tracking-wide")}
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Analyzing Speech Emotion...</span>
                    </>
                  ) : (
                    <span>Analyze Emotion</span>
                  )}
                </button>

                {!audioBlob && (
                  <p className="mt-2 text-center text-xs text-slate-400">
                    Upload or record speech to start analysis
                  </p>
                )}
              </div>

              {/* Error Callout */}
              {error && (
                <div className={cn(ui.alertError, "mt-4 flex items-start gap-2.5")}>
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-rose-900">Analysis Error</p>
                    <p className="mt-0.5 text-xs text-rose-700">{error}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Emotion Analysis Report (6 cols) */}
          <div className="lg:col-span-6 lg:sticky lg:top-20">
            <AnalysisReportPanel report={report} loading={analyzing} />
          </div>
        </div>
      </main>

      {/* Clean Minimal Footer */}
      <footer className="mt-12 border-t border-slate-200/60 py-6 text-center text-xs text-slate-400">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6">
          <p>Speech Emotion Recognition Studio</p>
          <div className="flex items-center gap-3 text-slate-400">
            <span>16 kHz Mono</span>
            <span>•</span>
            <span>Acoustic Prosody</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
