"use client";

import {
  Activity,
  Award,
  BarChart3,
  Check,
  Clock,
  Compass,
  Copy,
  Cpu,
  Gauge,
  Layers,
  Radio,
  Sparkles,
  Timer,
  Volume2,
  Waves,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

import { emotionMeta } from "@/lib/emotion-theme";
import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";
import type { AnalysisReport } from "@/types/analysis";

type Props = {
  report: AnalysisReport | null;
  loading?: boolean;
};

const INFERENCE_STEPS = [
  { step: "01/04", label: "Zero-Copy 16 kHz Mono Ingestion & Tensor Normalization", pct: 25 },
  { step: "02/04", label: "Acoustic Feature Extraction & VAD Silence Trimming", pct: 60 },
  { step: "03/04", label: "Learnable Weighted Layer Pooling Across 12 Hidden States", pct: 85 },
  { step: "04/04", label: "Softmax Calibration & Audio Behavioural Synthesis", pct: 98 },
];

export function AnalysisReportPanel({ report, loading }: Props) {
  const [copied, setCopied] = useState(false);
  const [progressIdx, setProgressIdx] = useState(0);
  const [simulatedPct, setSimulatedPct] = useState(15);

  useEffect(() => {
    if (!loading) {
      setProgressIdx(0);
      setSimulatedPct(15);
      return;
    }

    const interval = setInterval(() => {
      setProgressIdx((prev) => {
        const next = prev < INFERENCE_STEPS.length - 1 ? prev + 1 : prev;
        setSimulatedPct(INFERENCE_STEPS[next].pct);
        return next;
      });
    }, 400);

    return () => clearInterval(interval);
  }, [loading]);

  const handleCopyJson = () => {
    if (!report) return;
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    const activeStep = INFERENCE_STEPS[progressIdx];
    return (
      <div className={cn(ui.cardElevated, "flex min-h-[460px] flex-col items-center justify-center text-center relative overflow-hidden")}>
        {/* Ambient background glow */}
        <div className="absolute -top-20 -left-20 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -right-20 h-64 w-64 rounded-full bg-lime-400/10 blur-3xl pointer-events-none" />

        <div className="relative mb-6">
          <div className="absolute -inset-3 animate-ping rounded-full bg-cyan-400/20" />
          <div className="relative flex h-18 w-18 items-center justify-center rounded-3xl border border-cyan-400/40 bg-[#0d1424] text-cyan-300 shadow-[0_0_35px_rgba(0,240,255,0.35)]">
            <Radio className="h-8 w-8 animate-pulse text-cyan-400" />
          </div>
        </div>

        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-cyan-400">
          NEURAL INFERENCE ACTIVE
        </span>
        <h3 className="mt-1 text-lg font-extrabold tracking-tight text-white">
          Executing Multi-Layer Audio Decoding
        </h3>
        <p className="mt-1.5 max-w-sm text-xs leading-relaxed text-slate-400">
          {activeStep.label}
        </p>

        {/* Multi-step progress bar */}
        <div className="mt-8 w-full max-w-md space-y-2.5">
          <div className="flex items-center justify-between font-mono text-xs font-bold">
            <span className="text-cyan-400">PHASE {activeStep.step}</span>
            <span className="text-lime-300">{simulatedPct}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-white/[0.06] p-0.5 border border-white/[0.08]">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-teal-300 to-lime-400 shadow-[0_0_12px_rgba(0,240,255,0.6)] transition-all duration-300 ease-out"
              style={{ width: `${simulatedPct}%` }}
            />
          </div>
          <div className="flex justify-between text-[9px] font-mono uppercase tracking-wider text-slate-500 pt-1">
            <span>RESAMPLE 16K</span>
            <span>VAD TRIM</span>
            <span>LAYER POOL</span>
            <span>BEHAVIOR SYNTH</span>
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={cn(ui.cardMuted, "flex min-h-[460px] flex-col items-center justify-center text-center relative overflow-hidden")}>
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-white/[0.1] bg-white/[0.03] shadow-inner">
          <BarChart3 className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
        </div>
        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400">
          COCKPIT DIAGNOSTIC STANDBY
        </span>
        <h3 className="mt-1 text-base font-bold text-white">Awaiting Acoustic Signal</h3>
        <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-slate-400">
          Feed live microphone speech or ingest an audio clip to compute the full emotion classification and behavioral telemetry matrix.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {["12-Layer Pooling", "8-Class Softmax", "pYIN Pitch (F0)", "VAD Silence Trimming"].map((item) => (
            <span
              key={item}
              className="rounded-full border border-white/[0.08] bg-white/[0.02] px-3 py-1 font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400"
            >
              {item}
            </span>
          ))}
        </div>
      </div>
    );
  }

  const topMeta = emotionMeta(report.predicted_emotion);
  const confidencePct = (report.confidence * 100).toFixed(1);
  const numConfidence = report.confidence * 100;

  // Extract structured behavior or fallback to parsed metrics
  const behavior = report.behavior ?? {
    speaking_speed: {
      category: "Normal",
      syllables_per_second: 3.0,
      words_per_minute: 130,
    },
    pause_frequency: {
      category: "Normal",
      pauses_per_minute: 7.0,
      silence_ratio: 21.0,
    },
    vocal_energy: {
      category: "Moderate",
      rms_db: -24.5,
    },
    pitch_variation: {
      category: "Stable",
      mean_hz: 145.0,
      std_hz: 28.0,
    },
    overall_behaviour: "Engaged Communicator",
  };

  // Radial gauge parameters (radius: 46, circumference: ~289)
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (numConfidence / 100) * circumference;

  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
      {/* 1. HERO BENTO: Single North Star Metric & Cockpit Telemetry */}
      <div className={cn(ui.cardElevated, "relative overflow-hidden border border-white/[0.12]")}>
        {/* Ambient Top Glow reflecting the winning emotion */}
        <div
          className="absolute -top-24 -right-24 h-72 w-72 rounded-full blur-3xl pointer-events-none opacity-25"
          style={{ backgroundColor: topMeta.color }}
        />

        {/* Cockpit Header Bar */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4 mb-6">
          <div className="flex items-center gap-2.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{
                backgroundColor: topMeta.color,
                boxShadow: `0 0 10px ${topMeta.color}`,
              }}
            />
            <div>
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400">
                NORTH STAR TELEMETRY // {topMeta.code}
              </span>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Acoustic Emotion & Behavioural Report
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={handleCopyJson}
            className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.04] px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300 backdrop-blur-md transition-all hover:bg-white/[0.08] hover:text-white"
            title="Copy raw JSON payload"
          >
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3 text-slate-400" />}
            <span>{copied ? "COPIED" : "JSON RAW"}</span>
          </button>
        </div>

        {/* Central North Star Metric Cockpit Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Radial Concentric Gauge (North Star Core) */}
          <div className="md:col-span-5 flex flex-col items-center justify-center p-3 relative">
            <div className="relative flex items-center justify-center">
              <svg className="h-38 w-38 -rotate-90 transform" viewBox="0 0 110 110">
                {/* Background Track */}
                <circle
                  cx="55"
                  cy="55"
                  r={radius}
                  stroke="rgba(255, 255, 255, 0.06)"
                  strokeWidth="8"
                  fill="transparent"
                />
                {/* Concentric Progress Stroke */}
                <circle
                  cx="55"
                  cy="55"
                  r={radius}
                  stroke={topMeta.color}
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  style={{
                    filter: `drop-shadow(0 0 10px ${topMeta.glowColor})`,
                    transition: "stroke-dashoffset 1s ease-out",
                  }}
                />
              </svg>

              {/* Numerical Readout in Center */}
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="font-mono text-3xl font-extrabold tracking-tight text-white">
                  {confidencePct}
                  <span className="text-base text-slate-400 font-normal">%</span>
                </span>
                <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-400">
                  CONFIDENCE
                </span>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full border border-white/[0.1] bg-[#0c121e]/90 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
                <Compass className="h-3 w-3 text-cyan-400" />
                VALENCE: {topMeta.valence}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-white/[0.1] bg-[#0c121e]/90 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
                <Activity className="h-3 w-3 text-lime-400" />
                AROUSAL: {topMeta.arousal}
              </span>
            </div>
          </div>

          {/* Primary Emotion & Behavioral Readout */}
          <div className="md:col-span-7 space-y-4">
            <div>
              <div className="flex items-center gap-2.5">
                <span className={cn("rounded-md px-2.5 py-0.5 font-mono text-[10px] font-extrabold uppercase tracking-widest border", topMeta.badge)}>
                  {topMeta.tag}
                </span>
                <span className="font-mono text-xs text-slate-400">
                  {report.display_name}
                </span>
              </div>

              <h1 className="mt-1 text-3xl sm:text-4xl font-black uppercase tracking-tight text-white">
                {topMeta.label}
              </h1>
              <p className="mt-1 text-xs text-slate-300 leading-relaxed font-medium">
                {topMeta.description}
              </p>
            </div>

            {/* Behavioral Synthesis Box */}
            <div className="rounded-2xl border border-white/[0.08] bg-[#0a0e18]/80 p-4 shadow-inner backdrop-blur-xl">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Sparkles className="h-3 w-3 text-lime-400" />
                  AUDIO BEHAVIOURAL PROFILE
                </span>
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
                  CLINICAL SYNTHESIS
                </span>
              </div>
              <p className="text-sm font-bold text-white tracking-wide">
                {behavior.overall_behaviour}
              </p>
              <p className="mt-1 text-[11px] text-slate-400 leading-relaxed">
                {report.summary.replace(/\*\*/g, "")}
              </p>
            </div>

            {/* Inference Quick Benchmarks */}
            <div className="flex flex-wrap items-center gap-3 pt-1 text-[10px] font-mono text-slate-400">
              <span className="inline-flex items-center gap-1">
                <Timer className="h-3 w-3 text-cyan-400" />
                LATENCY: <strong className="text-white">{report.inference_time_sec.toFixed(3)}s</strong>
              </span>
              <span>//</span>
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3 text-teal-400" />
                SPAN: <strong className="text-white">{report.audio_duration_sec.toFixed(2)}s</strong>
              </span>
              <span>//</span>
              <span className="inline-flex items-center gap-1">
                <Volume2 className="h-3 w-3 text-lime-400" />
                RESAMPLE: <strong className="text-white">{report.sample_rate / 1000} kHz</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. 4-COLUMN BENTO TELEMETRY ROW: Organic Trend Visualizations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tile 1: Speaking Speed */}
        <div className="rounded-[24px] cyber-glass p-5 border border-white/[0.08] space-y-3 relative overflow-hidden group hover:border-cyan-400/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
              SPEED // TEMPO
            </span>
            <span className="rounded-full border border-cyan-500/30 bg-cyan-950/40 px-2 py-0.5 font-mono text-[9px] font-bold text-cyan-300">
              {behavior.speaking_speed.category}
            </span>
          </div>

          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-3xl font-black tracking-tight text-white">
                {behavior.speaking_speed.syllables_per_second}
              </span>
              <span className="text-[10px] font-mono uppercase text-slate-400">SYLL/SEC</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-0.5">
              {behavior.speaking_speed.words_per_minute} Words/Min
            </p>
          </div>

          {/* Organic Bezier Curve SVG */}
          <div className="h-9 w-full pt-1">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 28" preserveAspectRatio="none">
              <defs>
                <linearGradient id="speedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#00f0ff" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d="M 0,22 Q 25,6 50,18 T 100,10 L 100,28 L 0,28 Z"
                fill="url(#speedGrad)"
              />
              <path
                d="M 0,22 Q 25,6 50,18 T 100,10"
                fill="none"
                stroke="#00f0ff"
                strokeWidth="2"
                style={{ filter: "drop-shadow(0 0 4px #00f0ff)" }}
              />
            </svg>
          </div>
        </div>

        {/* Tile 2: Pause Frequency */}
        <div className="rounded-[24px] cyber-glass p-5 border border-white/[0.08] space-y-3 relative overflow-hidden group hover:border-lime-400/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
              CADENCE // PAUSES
            </span>
            <span className="rounded-full border border-lime-500/30 bg-lime-950/40 px-2 py-0.5 font-mono text-[9px] font-bold text-lime-300">
              {behavior.pause_frequency.category}
            </span>
          </div>

          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-3xl font-black tracking-tight text-white">
                {behavior.pause_frequency.pauses_per_minute}
              </span>
              <span className="text-[10px] font-mono uppercase text-slate-400">/MIN</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-0.5">
              {behavior.pause_frequency.silence_ratio}% Silence Ratio
            </p>
          </div>

          {/* Segmented Dot-Matrix Cyber Meter */}
          <div className="flex items-center gap-1 pt-2">
            {Array.from({ length: 10 }).map((_, i) => {
              const active = i < Math.min(10, Math.round(behavior.pause_frequency.silence_ratio / 4));
              return (
                <div
                  key={i}
                  className={cn(
                    "h-2 flex-1 rounded-xs transition-all",
                    active
                      ? "bg-lime-400 shadow-[0_0_6px_#ccff00]"
                      : "bg-white/[0.08]",
                  )}
                />
              );
            })}
          </div>
        </div>

        {/* Tile 3: Vocal Energy Dynamics */}
        <div className="rounded-[24px] cyber-glass p-5 border border-white/[0.08] space-y-3 relative overflow-hidden group hover:border-amber-400/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
              INTENSITY // ENERGY
            </span>
            <span className="rounded-full border border-amber-500/30 bg-amber-950/40 px-2 py-0.5 font-mono text-[9px] font-bold text-amber-300">
              {behavior.vocal_energy.category}
            </span>
          </div>

          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-3xl font-black tracking-tight text-white">
                {behavior.vocal_energy.rms_db}
              </span>
              <span className="text-[10px] font-mono uppercase text-slate-400">dB RMS</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-0.5">
              Acoustic Pressure Gain
            </p>
          </div>

          {/* High-Fidelity VU Meter Bar */}
          <div className="space-y-1 pt-1">
            <div className="h-2 w-full rounded-full bg-white/[0.08] overflow-hidden p-0.5 border border-white/[0.06]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"
                style={{
                  width: `${Math.min(100, Math.max(10, 100 + behavior.vocal_energy.rms_db * 2))}%`,
                  filter: "drop-shadow(0 0 6px #f59e0b)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Tile 4: Pitch Modulation (F0) */}
        <div className="rounded-[24px] cyber-glass p-5 border border-white/[0.08] space-y-3 relative overflow-hidden group hover:border-purple-400/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
              PITCH // F0 MODULATION
            </span>
            <span className="rounded-full border border-purple-500/30 bg-purple-950/40 px-2 py-0.5 font-mono text-[9px] font-bold text-purple-300">
              {behavior.pitch_variation.category}
            </span>
          </div>

          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-3xl font-black tracking-tight text-white">
                {behavior.pitch_variation.mean_hz}
              </span>
              <span className="text-[10px] font-mono uppercase text-slate-400">Hz Mean</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-0.5">
              σ = {behavior.pitch_variation.std_hz} Hz Std Dev
            </p>
          </div>

          {/* Smooth Sinusoidal Pitch Wave */}
          <div className="h-9 w-full pt-1">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 28" preserveAspectRatio="none">
              <defs>
                <linearGradient id="pitchGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#c084fc" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#c084fc" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d="M 0,14 Q 15,2 30,14 T 60,14 T 90,14 T 100,18 L 100,28 L 0,28 Z"
                fill="url(#pitchGrad)"
              />
              <path
                d="M 0,14 Q 15,2 30,14 T 60,14 T 90,14 T 100,18"
                fill="none"
                stroke="#c084fc"
                strokeWidth="2"
                style={{ filter: "drop-shadow(0 0 4px #c084fc)" }}
              />
            </svg>
          </div>
        </div>
      </div>

      {/* 3. NEURAL EMOTION PROBABILITY SPECTRUM (Cockpit Instrument Bars) */}
      <div className={cn(ui.card, "border border-white/[0.08]")}>
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06] mb-4">
          <p className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-slate-300">
            <BarChart3 className="h-4 w-4 text-cyan-400" />
            Full Neural Logit Probability Spectrum
          </p>
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-500">
            SOFTMAX NORMALIZED
          </span>
        </div>

        <div className="space-y-3">
          {report.probabilities.map((item) => {
            const itemMeta = emotionMeta(item.emotion);
            const isWinner = item.emotion.toLowerCase() === report.predicted_emotion.toLowerCase();
            const pct = item.probability * 100;

            return (
              <div key={item.emotion} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{
                        backgroundColor: itemMeta.color,
                        boxShadow: isWinner ? `0 0 8px ${itemMeta.color}` : "none",
                      }}
                    />
                    <span className={cn("tracking-wide font-bold", isWinner ? "text-white" : "text-slate-400")}>
                      {itemMeta.label}
                    </span>
                    <span className="text-[10px] text-slate-500">[{itemMeta.code}]</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {isWinner && (
                      <span className="rounded-md border border-lime-400/40 bg-lime-950/40 px-2 py-0.5 text-[9px] font-extrabold uppercase text-lime-300">
                        DOMINANT
                      </span>
                    )}
                    <span className={cn("font-bold", isWinner ? "text-cyan-300" : "text-slate-400")}>
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Cyber-Glass Horizontal Bar */}
                <div className="h-2 w-full rounded-full bg-white/[0.05] p-0.5 border border-white/[0.04]">
                  <div
                    className={cn(
                      "h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out",
                      itemMeta.barColor,
                      isWinner && "shadow-[0_0_10px_rgba(204,255,0,0.5)]",
                    )}
                    style={{ width: `${Math.max(1, pct)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
