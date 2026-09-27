"use client";

import {
  Activity,
  AlertCircle,
  AudioWaveform,
  CheckCircle2,
  Cpu,
  Layers,
  Loader2,
  Mic,
  Radio,
  RefreshCw,
  Sparkles,
  Trash2,
  Upload,
  Volume2,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioUploader } from "@/components/AudioUploader";
import { AnalysisReportPanel } from "@/components/AnalysisReportPanel";
import { CyberAudioVisualizer } from "@/components/CyberAudioVisualizer";
import { ModelSelector } from "@/components/ModelSelector";
import { analyzeAudio, checkApiHealth, fetchModels } from "@/lib/api";
import { cn } from "@/lib/cn";
import { emotionMeta } from "@/lib/emotion-theme";
import { ui } from "@/lib/ui";
import type { AnalysisReport, InputMode, ModelInfo } from "@/types/analysis";

const FALLBACK_MODELS: ModelInfo[] = [
  {
    key: "mfcc_lstm",
    display_name: "MFCC + LSTM",
    input_type: "mfcc",
    architecture: "MFCC(40) -> Bi-LSTM(256x2) -> Linear(8)",
    checkpoint_available: true,
  },
  {
    key: "wav2vec2_xlsr_300m",
    display_name: "Wav2Vec2-XLS-R-300M",
    input_type: "waveform",
    architecture: "Wav2Vec2-XLS-R -> Masked Avg Pool -> Linear(8)",
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
      setError(err instanceof Error ? err.message : "Inference telemetry pipeline failed.");
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
      {/* Top Futuristic Cockpit Navigation Bar */}
      <header className={ui.header}>
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-3.5">
            {/* Holographic Logo Hex Icon */}
            <div className="relative flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-600/30 to-violet-600/30 border border-cyan-400/40 text-cyan-300 shadow-[0_0_20px_rgba(0,240,255,0.25)]">
              <AudioWaveform className="h-5 w-5 animate-pulse text-cyan-300" strokeWidth={2.2} />
              <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border border-black bg-[#00f59b] shadow-[0_0_8px_#00f59b]" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-extrabold tracking-wider text-white">
                  AURA <span className="text-[#00f0ff]">CYBER-GLASS</span>
                </span>
                <span className="rounded-full bg-cyan-950/60 px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest text-cyan-300 ring-1 ring-cyan-500/40">
                  SYSTEM v3.0
                </span>
              </div>
              <p className="font-mono text-[10px] tracking-wider text-slate-400 uppercase">
                Neural Speech Emotion & Behavioral Prosody Intelligence
              </p>
            </div>
          </div>

          {/* Cockpit Status Pill Telemetry */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Live Accelerator Badge */}
            <div className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-cyan-500/20 bg-[#0c121e]/90 px-3 py-1 text-[11px] font-mono text-cyan-300 shadow-inner">
              <Cpu className="h-3.5 w-3.5 text-cyan-400" />
              <span>MPS ACCELERATOR // ACTIVE</span>
            </div>

            {/* API Health Status */}
            <div
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[11px] font-medium backdrop-blur-md transition-all",
                apiOnline === true && "border-emerald-500/30 bg-emerald-950/40 text-emerald-300 shadow-[0_0_12px_rgba(0,245,155,0.15)]",
                apiOnline === false && "border-amber-500/30 bg-amber-950/40 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.15)]",
                apiOnline === null && "border-slate-800 bg-slate-900/60 text-slate-400",
              )}
            >
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  apiOnline === true && "bg-[#00f59b] shadow-[0_0_8px_#00f59b]",
                  apiOnline === false && "bg-amber-400 animate-pulse",
                  apiOnline === null && "animate-pulse bg-slate-400",
                )}
              />
              <span>
                {apiOnline ? "INFERENCE API ONLINE (8000)" : apiOnline === false ? "LOCAL API OFFLINE" : "SYNCING ENGINES..."}
              </span>
            </div>

            {/* Quick Refresh Trigger */}
            <button
              type="button"
              onClick={refreshSystem}
              title="Refresh Engine Telemetry"
              className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-700/60 bg-[#0f172a]/80 text-slate-300 hover:border-cyan-400/50 hover:text-cyan-300 transition-all"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", modelsLoading && "animate-spin text-cyan-400")} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Bento Grid Architecture */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 pb-28">
        {/* Top 3D Spatial Hero Tile */}
        <section className="mb-6 overflow-hidden rounded-3xl cyber-glass p-5 relative">
          <div className="grid grid-cols-1 items-center gap-6 lg:grid-cols-12">
            {/* Spatial 3D Gyroscope & Wave Visualizer */}
            <div className="relative flex flex-col items-center justify-center lg:col-span-5">
              <div className="absolute top-2 left-2 flex items-center gap-2 font-mono text-[10px] tracking-widest uppercase text-cyan-400">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
                <span>3D GYROSCOPIC ACOUSTIC CORE</span>
              </div>

              <CyberAudioVisualizer
                isActive={Boolean(audioBlob) || analyzing}
                intensity={analyzing ? 1.0 : audioBlob ? 0.65 : 0.3}
                primaryColor={activeEmotionTheme?.color ?? "#00f0ff"}
                glowColor={activeEmotionTheme?.glowColor ?? "rgba(0, 240, 255, 0.4)"}
                emotionLabel={report?.predicted_emotion ? activeEmotionTheme?.label : undefined}
                className="w-full h-48 sm:h-52"
              />

              <div className="text-center mt-1">
                <p className="font-mono text-[11px] text-slate-400">
                  {analyzing ? (
                    <span className="text-[#ccff00] font-bold animate-pulse">EXTRACTING PROSODIC TENSORS...</span>
                  ) : report ? (
                    <span className="text-cyan-300 font-medium">RESONATING TO {activeEmotionTheme?.label?.toUpperCase()} VECTOR</span>
                  ) : audioBlob ? (
                    <span className="text-slate-300">AUDIO SIGNAL LOADED // READY FOR INFERENCE</span>
                  ) : (
                    <span className="text-slate-500">STANDBY MODE // AWAITING AUDIO FEED</span>
                  )}
                </p>
              </div>
            </div>

            {/* Spatial Telemetry & Physical-To-Digital Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 lg:col-span-7">
              <div className="rounded-2xl border border-white/5 bg-[#090d16]/70 p-3.5">
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Latency Overhead</span>
                <div className="mt-1 text-xl font-bold font-mono text-cyan-300">~38.4 ms</div>
                <div className="mt-0.5 text-[10px] text-slate-400">Real-time MPS execution</div>
              </div>

              <div className="rounded-2xl border border-white/5 bg-[#090d16]/70 p-3.5">
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Sampling Rate</span>
                <div className="mt-1 text-xl font-bold font-mono text-emerald-400">16,000 Hz</div>
                <div className="mt-0.5 text-[10px] text-slate-400">Nyquist standard 8 kHz BW</div>
              </div>

              <div className="rounded-2xl border border-white/5 bg-[#090d16]/70 p-3.5">
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Audio Channels</span>
                <div className="mt-1 text-xl font-bold font-mono text-[#ccff00]">1.0 Mono</div>
                <div className="mt-0.5 text-[10px] text-slate-400">Normalized amplitude 32-bit</div>
              </div>

              <div className="rounded-2xl border border-white/5 bg-[#090d16]/70 p-3.5">
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Emotion Space</span>
                <div className="mt-1 text-xl font-bold font-mono text-rose-400">8 Classes</div>
                <div className="mt-0.5 text-[10px] text-slate-400">RAVDESS 2D Circumplex</div>
              </div>
            </div>
          </div>
        </section>

        {/* 2-Column Bento Grid: Input Station vs Diagnostic Panel */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left Column: Input Station & Model Controls (7 cols) */}
          <div className="space-y-6 lg:col-span-6 xl:col-span-7">
            {/* Input Station Card */}
            <div className={ui.cardElevated}>
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-[#00f0ff] shadow-[0_0_8px_#00f0ff]" />
                    <h2 className={ui.sectionTitle}>Audio Ingestion Station</h2>
                  </div>
                  <p className={ui.sectionDesc}>Select input vector medium to feed the neural encoder</p>
                </div>

                {audioBlob && (
                  <button
                    type="button"
                    onClick={clearAudio}
                    title="Eject audio"
                    className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/30 bg-rose-950/40 px-2.5 py-1 font-mono text-[10px] font-bold text-rose-300 hover:bg-rose-900/50 transition-all"
                  >
                    <Trash2 className="h-3 w-3" />
                    <span>Eject</span>
                  </button>
                )}
              </div>

              {/* Segmented Mode Tabs (Cyber-Pills) */}
              <div className={cn(ui.segmentWrap, "mb-5")}>
                <button
                  type="button"
                  onClick={() => switchTab("upload")}
                  className={cn(
                    "inline-flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-all",
                    inputTab === "upload" ? ui.segmentActive : ui.segmentIdle,
                  )}
                >
                  <Upload className="h-3.5 w-3.5" strokeWidth={2.2} />
                  <span>Upload Audio File</span>
                </button>
                <button
                  type="button"
                  onClick={() => switchTab("record")}
                  className={cn(
                    "inline-flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-all",
                    inputTab === "record" ? ui.segmentActive : ui.segmentIdle,
                  )}
                >
                  <Mic className="h-3.5 w-3.5" strokeWidth={2.2} />
                  <span>Record Live Speech</span>
                </button>
              </div>

              {/* Ingestion Canvas */}
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

              {/* Model Intelligence Selector Tile */}
              <div className="mt-6 border-t border-white/10 pt-5">
                <ModelSelector
                  models={models}
                  value={modelKey}
                  onChange={setModelKey}
                  loading={modelsLoading}
                />
              </div>

              {/* Primary In-Card Action CTA */}
              <div className="mt-6">
                <button
                  type="button"
                  disabled={!canAnalyze || apiOnline === false}
                  onClick={runAnalysis}
                  className={cn(
                    ui.btnPrimary,
                    "w-full py-4 text-base font-extrabold tracking-wider",
                    canAnalyze && "glow-lime ring-1 ring-lime-400/40",
                  )}
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin text-black" />
                      <span>RUNNING NEURAL INFERENCE...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5 text-black" />
                      <span>ANALYZE EMOTION & PROSODY</span>
                    </>
                  )}
                </button>

                {!audioBlob && (
                  <p className="mt-2 text-center font-mono text-[11px] text-slate-500">
                    Ingest an audio signal or select a Hindi sample above to activate neural pipeline
                  </p>
                )}
              </div>

              {/* Error Callout */}
              {error && (
                <div className={cn(ui.alertError, "mt-4 flex gap-2.5")}>
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" />
                  <div>
                    <p className="font-bold text-rose-200">Pipeline Ingestion Exception</p>
                    <p className="mt-0.5 font-mono text-xs text-rose-300">{error}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Single North Star Diagnostic Telemetry (5 cols) */}
          <div className="lg:col-span-6 xl:col-span-5">
            <div className="lg:sticky lg:top-24">
              <AnalysisReportPanel report={report} loading={analyzing} />
            </div>
          </div>
        </div>
      </main>

      {/* Ergonomic "Thumb Zone" Action Pod (Floating Mobile & Desktop Pill) */}
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 w-full max-w-xl px-4 pointer-events-none">
        <div className="pointer-events-auto rounded-3xl cyber-glass-elevated border border-white/20 p-2.5 shadow-[0_12px_40px_rgba(0,0,0,0.85)] backdrop-blur-2xl flex items-center justify-between gap-3">
          {/* Signal Indicator & Audio Status */}
          <div className="flex items-center gap-2.5 pl-2 overflow-hidden">
            <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-[#090d16] text-cyan-300">
              {analyzing ? (
                <Loader2 className="h-4 w-4 animate-spin text-[#ccff00]" />
              ) : audioBlob ? (
                <Volume2 className="h-4 w-4 text-[#00f59b]" />
              ) : (
                <Radio className="h-4 w-4 text-slate-500" />
              )}
            </div>
            <div className="min-w-0 pr-1">
              <div className="truncate font-mono text-xs font-semibold text-slate-200">
                {audioBlob ? audioName || "Audio Signal Ready" : "Awaiting Audio Stream"}
              </div>
              <div className="font-mono text-[10px] text-slate-400">
                {analyzing
                  ? "Evaluating spectrogram tensors..."
                  : audioBlob
                  ? `${selectedModel?.display_name || "Model Ready"}`
                  : "Upload file or speak"}
              </div>
            </div>
          </div>

          {/* Thumb-Zone Trigger Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {audioBlob && (
              <button
                type="button"
                onClick={clearAudio}
                className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-slate-900/80 text-slate-400 hover:text-rose-400 hover:border-rose-500/40 transition-all"
                title="Eject Audio"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}

            <button
              type="button"
              disabled={!canAnalyze || apiOnline === false}
              onClick={runAnalysis}
              className={cn(
                "inline-flex items-center gap-2 rounded-2xl px-5 py-2.5 font-mono text-xs font-black tracking-wider transition-all",
                canAnalyze
                  ? "bg-[#ccff00] text-black shadow-[0_0_20px_rgba(204,255,0,0.5)] hover:scale-102 active:scale-98"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed",
              )}
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>INFERRING</span>
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 fill-black" />
                  <span>ANALYZE</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Cyber Cockpit Footer */}
      <footer className="border-t border-white/10 bg-[#06080d]/90 py-5 text-center text-xs text-slate-400 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#00f0ff]" />
            <span className="font-mono text-[11px] text-slate-300">
              AURA CYBER-GLASS PLATFORM // SPEECH EMOTION DETECTION
            </span>
          </div>
          <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
            <span>Actor-Independent Split</span>
            <span>//</span>
            <span>16 kHz Mono PCM</span>
            <span>//</span>
            <span>Bento Cockpit Architecture</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
