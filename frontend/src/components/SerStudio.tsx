"use client";

import {
  Activity,
  AlertCircle,
  ArrowRight,
  ArrowUpRight,
  AudioWaveform,
  CheckCircle2,
  ChevronRight,
  Compass,
  Cpu,
  Flame,
  Globe,
  Layers,
  LayoutGrid,
  Loader2,
  Mic,
  Play,
  Radio,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sliders,
  Sparkles,
  Square,
  Trash2,
  Upload,
  User,
  Volume2,
  Waves,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioUploader } from "@/components/AudioUploader";
import { AnalysisReportPanel } from "@/components/AnalysisReportPanel";
import { ArcTrajectoryGraph } from "@/components/ArcTrajectoryGraph";
import { CyberAudioVisualizer } from "@/components/CyberAudioVisualizer";
import { DotMatrixNumber } from "@/components/DotMatrixNumber";
import { ModelSelector } from "@/components/ModelSelector";
import { analyzeAudio, checkApiHealth, fetchModels } from "@/lib/api";
import { cn } from "@/lib/cn";
import { emotionMeta } from "@/lib/emotion-theme";
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
  const [activeNav, setActiveNav] = useState<"dashboard" | "inference" | "models" | "research">("dashboard");
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

  const activeEmotionTheme = useMemo(() => {
    if (!report?.predicted_emotion) return null;
    return emotionMeta(report.predicted_emotion);
  }, [report]);

  const runAnalysis = async () => {
    if (!audioBlob || !selectedModel?.checkpoint_available) return;
    setAnalyzing(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyzeAudio(modelKey, audioBlob, audioName || "audio.wav");
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inference pipeline failed.");
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
      <div className="flex">
        {/* Left Tactile Icon Dock (Matching the Monitor Mockup Sidebar) */}
        <aside className="hidden lg:flex w-20 flex-col items-center justify-between py-6 px-3 border-r border-white/6 bg-[#06070a]/90 backdrop-blur-2xl sticky top-0 h-screen z-40">
          <div className="flex flex-col items-center gap-5 w-full">
            {/* Top Brand Glyph in circle */}
            <div className="h-10 w-10 rounded-full bg-white/10 border border-white/15 flex items-center justify-center text-white shadow-md">
              <AudioWaveform className="h-5 w-5 stroke-[2.2]" />
            </div>

            {/* Vertical Pill Dock Container */}
            <div className="flex flex-col items-center gap-3.5 p-2 rounded-full bg-white/[0.04] border border-white/8 backdrop-blur-xl">
              {/* Active Blue Circle Button */}
              <button
                type="button"
                onClick={() => setActiveNav("dashboard")}
                title="Dashboard"
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all",
                  activeNav === "dashboard"
                    ? "bg-[#2563eb] text-white shadow-[0_4px_16px_rgba(37,99,235,0.4)]"
                    : "text-slate-400 hover:text-white hover:bg-white/8",
                )}
              >
                <LayoutGrid className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={() => setActiveNav("inference")}
                title="Inference Station"
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all",
                  activeNav === "inference"
                    ? "bg-[#2563eb] text-white shadow-[0_4px_16px_rgba(37,99,235,0.4)]"
                    : "text-slate-400 hover:text-white hover:bg-white/8",
                )}
              >
                <Activity className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={() => setActiveNav("models")}
                title="Neural Models"
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all",
                  activeNav === "models"
                    ? "bg-[#2563eb] text-white shadow-[0_4px_16px_rgba(37,99,235,0.4)]"
                    : "text-slate-400 hover:text-white hover:bg-white/8",
                )}
              >
                <Compass className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={() => setActiveNav("research")}
                title="Prosody Analytics"
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all",
                  activeNav === "research"
                    ? "bg-[#2563eb] text-white shadow-[0_4px_16px_rgba(37,99,235,0.4)]"
                    : "text-slate-400 hover:text-white hover:bg-white/8",
                )}
              >
                <Waves className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={runAnalysis}
                disabled={!canAnalyze}
                title="Trigger Analysis"
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all",
                  canAnalyze
                    ? "bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] hover:scale-105"
                    : "text-slate-600 cursor-not-allowed",
                )}
              >
                <Zap className="h-4 w-4 fill-current" />
              </button>
            </div>
          </div>

          {/* Bottom Refresh Action in Circle */}
          <button
            type="button"
            onClick={refreshSystem}
            title="Reset / Sync Engine"
            className="h-10 w-10 rounded-full bg-white/6 border border-white/10 text-slate-400 hover:text-white hover:bg-white/12 flex items-center justify-center transition-all"
          >
            <RotateCcw className={cn("h-4 w-4", modelsLoading && "animate-spin text-white")} />
          </button>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 min-w-0">
          {/* Top Pill Navigation Bar (Matching Monitor Mockup) */}
          <header className={ui.header}>
            <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
              {/* Left Brand Identity */}
              <div className="flex items-center gap-3">
                <div className="lg:hidden h-9 w-9 rounded-full bg-white/10 border border-white/15 flex items-center justify-center text-white">
                  <AudioWaveform className="h-4 w-4" />
                </div>
                <div>
                  <h1 className="text-sm font-semibold tracking-tight text-white">
                    AURA <span className="text-slate-400 font-normal">SER Studio</span>
                  </h1>
                </div>
              </div>

              {/* Center Floating Pill Group (Exact RonDesignLab Navigation) */}
              <nav className="flex items-center gap-1 rounded-full bg-white/6 border border-white/8 p-1 backdrop-blur-xl">
                <button
                  type="button"
                  onClick={() => setActiveNav("dashboard")}
                  className={cn(
                    "rounded-full px-5 py-1.5 text-xs font-semibold transition-all",
                    activeNav === "dashboard" ? ui.pillWhiteActive : ui.pillIdle,
                  )}
                >
                  Dashboard
                </button>
                <button
                  type="button"
                  onClick={() => setActiveNav("inference")}
                  className={cn(
                    "rounded-full px-5 py-1.5 text-xs font-semibold transition-all",
                    activeNav === "inference" ? ui.pillWhiteActive : ui.pillIdle,
                  )}
                >
                  Inference Hub
                </button>
                <button
                  type="button"
                  onClick={() => setActiveNav("models")}
                  className={cn(
                    "rounded-full px-5 py-1.5 text-xs font-semibold transition-all hidden sm:block",
                    activeNav === "models" ? ui.pillWhiteActive : ui.pillIdle,
                  )}
                >
                  Neural Models
                </button>
                <button
                  type="button"
                  onClick={() => setActiveNav("research")}
                  className={cn(
                    "rounded-full px-5 py-1.5 text-xs font-semibold transition-all hidden md:block",
                    activeNav === "research" ? ui.pillWhiteActive : ui.pillIdle,
                  )}
                >
                  Behavior Hub
                </button>
              </nav>

              {/* Right Telemetry Badge */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 rounded-full border border-white/8 bg-white/4 px-3 py-1 font-mono text-[11px] text-slate-300">
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      apiOnline === true && "bg-emerald-400 shadow-[0_0_8px_#34d399]",
                      apiOnline === false && "bg-amber-400 animate-pulse",
                      apiOnline === null && "bg-slate-400 animate-pulse",
                    )}
                  />
                  <span className="hidden sm:inline">
                    {apiOnline ? "MPS Accelerated" : apiOnline === false ? "Local Offline" : "Connecting..."}
                  </span>
                </div>
              </div>
            </div>
          </header>

          {/* Main Studio Grid */}
          <main className="mx-auto max-w-7xl px-4 py-7 sm:px-6 space-y-7">
            {/* Top Hero Row: 3 Organic Squircle Cards (Matching Monitor Mockup Hero Row) */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-stretch">
              {/* Card 1: 3D Holographic Gyroscopic Acoustic Core (Col 5) */}
              <div className="md:col-span-5 rounded-[36px] squircle-obsidian p-6 relative overflow-hidden flex flex-col justify-between border border-white/8 min-h-[360px]">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-white shadow-[0_0_8px_#ffffff]" />
                    <span className="text-xs font-semibold text-white tracking-wide">
                      Acoustic Core
                    </span>
                  </div>
                  <span className="rounded-full bg-white/6 border border-white/10 px-2.5 py-0.5 font-mono text-[9px] text-slate-300">
                    16,000 Hz Mono
                  </span>
                </div>

                {/* 3D Visualizer Orb */}
                <div className="my-auto py-2">
                  <CyberAudioVisualizer
                    isActive={Boolean(audioBlob) || analyzing}
                    intensity={analyzing ? 1.0 : audioBlob ? 0.7 : 0.25}
                    primaryColor={activeEmotionTheme?.color ?? "#ffffff"}
                    glowColor={activeEmotionTheme?.glowColor ?? "rgba(255, 255, 255, 0.4)"}
                    emotionLabel={report?.predicted_emotion ? activeEmotionTheme?.label : undefined}
                    className="w-full h-44"
                  />
                </div>

                {/* Audio Status Pill (like Bank Account pill in the reference card) */}
                <div className="rounded-2xl bg-white/[0.06] border border-white/10 p-3 flex items-center justify-between gap-3 backdrop-blur-xl">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="h-8 w-8 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center shrink-0">
                      <Volume2 className="h-4 w-4 text-white" />
                    </div>
                    <div className="truncate">
                      <p className="truncate text-xs font-semibold text-white">
                        {audioName || "No Audio Loaded"}
                      </p>
                      <p className="font-mono text-[10px] text-slate-400">
                        {audioBlob ? "Ready for inference" : "Upload speech sample"}
                      </p>
                    </div>
                  </div>

                  {audioBlob ? (
                    <button
                      type="button"
                      onClick={clearAudio}
                      className="btn-circle-dark shrink-0"
                      title="Clear audio"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-slate-300" />
                    </button>
                  ) : (
                    <div className="btn-circle-dark shrink-0">
                      <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                  )}
                </div>
              </div>

              {/* Card 2: Radiant Magenta Hero Squircle (Dominant Resonance / North Star) (Col 7) */}
              <div className="md:col-span-7">
                <AnalysisReportPanel report={report} loading={analyzing} />
              </div>
            </div>

            {/* Bottom Bento Row: Brands / Models / Ingestion Shelf (Matching Monitor Bottom Shelf) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* Left 7 Cols: Audio Ingestion Station */}
              <div className="lg:col-span-7 rounded-[36px] squircle-obsidian p-6 sm:p-7 border border-white/8 space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                      Speech Ingestion Station
                    </h2>
                    <p className="mt-0.5 text-xs text-slate-400">
                      Upload audio recording, use Hindi benchmark samples, or record live speech
                    </p>
                  </div>

                  {/* Mode Selector Pill Tabs */}
                  <div className="flex items-center gap-1 rounded-full bg-white/6 border border-white/10 p-1">
                    <button
                      type="button"
                      onClick={() => switchTab("upload")}
                      className={cn(
                        "rounded-full px-4 py-1.5 text-xs font-semibold transition-all flex items-center gap-1.5",
                        inputTab === "upload" ? ui.pillWhiteActive : ui.pillIdle,
                      )}
                    >
                      <Upload className="h-3.5 w-3.5" />
                      <span>Upload</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => switchTab("record")}
                      className={cn(
                        "rounded-full px-4 py-1.5 text-xs font-semibold transition-all flex items-center gap-1.5",
                        inputTab === "record" ? ui.pillWhiteActive : ui.pillIdle,
                      )}
                    >
                      <Mic className="h-3.5 w-3.5" />
                      <span>Record</span>
                    </button>
                  </div>
                </div>

                {/* Tab Ingestion Area */}
                <div>
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
                </div>

                {/* Model Selector Row */}
                <div className="pt-2 border-t border-white/8">
                  <ModelSelector
                    models={models}
                    value={modelKey}
                    onChange={setModelKey}
                    loading={modelsLoading}
                  />
                </div>

                {/* Primary Action Button (Clean White Minimal Pill) */}
                <div className="pt-1">
                  <button
                    type="button"
                    disabled={!canAnalyze || apiOnline === false}
                    onClick={runAnalysis}
                    className={cn(
                      ui.btnPrimary,
                      "w-full py-3.5 text-xs tracking-wider",
                    )}
                  >
                    {analyzing ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>PROCESSING INFERENCE...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 fill-black" />
                        <span>ANALYZE SPEECH EMOTION</span>
                      </>
                    )}
                  </button>
                </div>

                {error && (
                  <div className={cn(ui.alertError, "flex items-start gap-2.5")}>
                    <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-rose-200">Execution Error</p>
                      <p className="font-mono text-xs text-rose-300 mt-0.5">{error}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Right 5 Cols: Benchmarks & Architecture Card (Matching Brands / Tasks Shelf) */}
              <div className="lg:col-span-5 rounded-[36px] squircle-obsidian p-6 sm:p-7 border border-white/8 flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                      Model Pipeline & Datasets
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">
                      8-Class / 5-Class
                    </span>
                  </div>

                  <div className="space-y-3">
                    {/* Item 1: Hindi Specialist */}
                    <div className="rounded-2xl bg-white/[0.04] border border-white/8 p-3.5 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-white text-black font-mono font-bold text-xs flex items-center justify-center shadow-sm">
                          5
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-white">Hindi Emotion Specialist</p>
                          <p className="font-mono text-[10px] text-slate-400">MFCC(40) + CNN-BiLSTM</p>
                        </div>
                      </div>
                      <span className="font-mono text-xs font-medium text-slate-300">
                        86.8% Acc
                      </span>
                    </div>

                    {/* Item 2: Wav2Vec2 Foundation */}
                    <div className="rounded-2xl bg-white/[0.04] border border-white/8 p-3.5 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-white/10 text-white font-mono font-bold text-xs flex items-center justify-center">
                          8
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-white">Wav2Vec2 XLS-R 300M</p>
                          <p className="font-mono text-[10px] text-slate-400">Layer-Weighted Pooling</p>
                        </div>
                      </div>
                      <span className="font-mono text-xs font-medium text-slate-400">
                        300M Params
                      </span>
                    </div>

                    {/* Item 3: RAVDESS Benchmark */}
                    <div className="rounded-2xl bg-white/[0.04] border border-white/8 p-3.5 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-white/10 text-white font-mono font-bold text-xs flex items-center justify-center">
                          24
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-white">Actor-Independent Split</p>
                          <p className="font-mono text-[10px] text-slate-400">Strict Cross-Validation</p>
                        </div>
                      </div>
                      <span className="font-mono text-xs font-medium text-slate-400">
                        Macro-F1
                      </span>
                    </div>
                  </div>
                </div>

                {/* Subtle timeline track preview (like Brand Tasks timeline in the monitor image) */}
                <div className="pt-4 border-t border-white/8">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2">
                    <span className="font-medium text-slate-300">Telemetry Stream</span>
                    <span className="font-mono text-[10px]">~38.4 ms Latency</span>
                  </div>
                  <div className="relative h-1.5 w-full bg-white/8 rounded-full overflow-hidden">
                    <div className="h-full bg-white w-2/3 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          </main>

          {/* Minimal Subtle Footer */}
          <footer className="border-t border-white/6 bg-[#06070a] py-6 text-center text-xs text-slate-500">
            <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 sm:flex-row sm:px-6 font-mono text-[10px]">
              <p>AURA NEURAL SER · MINIMAL PREMIUM INSTRUMENTATION</p>
              <div className="flex items-center gap-3 text-slate-400">
                <span>16 kHz PCM</span>
                <span>•</span>
                <span>Actor-Independent</span>
                <span>•</span>
                <span>pYIN Prosody</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
