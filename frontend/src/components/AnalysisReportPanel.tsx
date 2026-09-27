"use client";

import {
  Activity,
  ArrowUpRight,
  Check,
  Compass,
  Copy,
  Info,
  Radio,
  Sliders,
  Sparkles,
  Volume2,
  Waves,
  Zap,
} from "lucide-react";
import { useState } from "react";

import { ArcTrajectoryGraph } from "@/components/ArcTrajectoryGraph";
import { DotMatrixNumber } from "@/components/DotMatrixNumber";
import { cn } from "@/lib/cn";
import { emotionMeta } from "@/lib/emotion-theme";
import { ui } from "@/lib/ui";
import type { AnalysisReport } from "@/types/analysis";

type Props = {
  report: AnalysisReport | null;
  loading?: boolean;
};

export function AnalysisReportPanel({ report, loading }: Props) {
  const [copied, setCopied] = useState(false);
  const [visualMode, setVisualMode] = useState<"arcs" | "dot-grid">("arcs");

  const handleCopyJson = () => {
    if (!report) return;
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="rounded-[36px] squircle-obsidian p-8 sm:p-10 flex min-h-[460px] flex-col items-center justify-center text-center relative overflow-hidden border border-white/10">
        {/* Ambient subtle violet glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-violet-600/10 blur-3xl pointer-events-none" />

        <div className="relative mb-6">
          <div className="h-16 w-16 rounded-full bg-white/5 border border-white/15 flex items-center justify-center shadow-lg">
            <Radio className="h-7 w-7 animate-pulse text-white" />
          </div>
        </div>

        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
          Inference Telemetry
        </span>
        <h3 className="mt-1 text-base font-semibold text-white tracking-tight">
          Decoding Acoustic Tensors
        </h3>
        <p className="mt-1.5 max-w-xs text-xs text-slate-400 leading-relaxed">
          Extracting log-mel spectrogram features and evaluating prosody matrices.
        </p>

        {/* Minimal dot-matrix loader indicator */}
        <div className="mt-8 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-white animate-ping" />
          <span className="h-2 w-2 rounded-full bg-white/60 animate-pulse" />
          <span className="h-2 w-2 rounded-full bg-white/30" />
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="rounded-[36px] squircle-obsidian p-8 sm:p-10 flex min-h-[460px] flex-col items-center justify-center text-center relative overflow-hidden border border-white/10">
        <div className="h-16 w-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-5 text-slate-400">
          <Activity className="h-7 w-7 stroke-[1.5]" />
        </div>

        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
          Standby Engine
        </span>
        <h3 className="mt-1 text-base font-semibold text-white tracking-tight">
          Awaiting Audio Signal
        </h3>
        <p className="mt-1.5 max-w-xs text-xs text-slate-400 leading-relaxed">
          Ingest a speech recording or select a benchmark sample to activate neural decoding.
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-2">
          {["16 kHz Mono", "8-Class Circumplex", "F0 Prosody", "Speech Rate"].map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-white/8 bg-white/3 px-3 py-1 font-mono text-[9px] uppercase tracking-wider text-slate-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    );
  }

  const topMeta = emotionMeta(report.predicted_emotion);
  const confidencePct = (report.confidence * 100).toFixed(1);

  const behavior = report.behavior ?? {
    speaking_speed: {
      category: "Normal",
      syllables_per_second: 2.7,
      words_per_minute: 108,
    },
    pause_frequency: {
      category: "Moderate",
      pauses_per_minute: 12.0,
      silence_ratio: 22.4,
    },
    vocal_energy: {
      category: "Moderate",
      rms_db: -24.9,
    },
    pitch_variation: {
      category: "Stable",
      mean_hz: 110.0,
      std_hz: 19.5,
    },
    overall_behaviour: "Engaged Communicator",
  };

  return (
    <div className="space-y-5 animate-in fade-in zoom-in-95 duration-300">
      {/* 1. HERO SQUIRCLE CARD: Radiant Plum/Magenta Minimal Hero (like Total Balance & Lung Capacity) */}
      <div className="squircle-magenta p-6 sm:p-7 relative overflow-hidden transition-all duration-300">
        {/* Top Header Row */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-white/80 tracking-wide">
              Dominant Resonance
            </span>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-xs font-bold text-white tracking-wider">
                {topMeta.label.toUpperCase()}
              </span>
              <span className="rounded-full bg-black/30 border border-white/15 px-2 py-0.5 text-[9px] font-mono text-white/90">
                {topMeta.code}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setVisualMode((m) => (m === "arcs" ? "dot-grid" : "arcs"))}
              title="Toggle graph visualizer mode"
              className="h-8 w-8 rounded-full bg-black/30 border border-white/20 text-white/80 hover:text-white flex items-center justify-center transition-all"
            >
              <Sliders className="h-3.5 w-3.5" />
            </button>
            <div className="btn-circle-white">
              <ArrowUpRight className="h-4 w-4 stroke-[2.2]" />
            </div>
          </div>
        </div>

        {/* Sub-row: Sample stats & coordinates */}
        <div className="mt-4 flex items-center justify-between text-[11px] text-white/70 font-mono">
          <div className="flex items-center gap-1.5">
            <DotMatrixNumber value="15" size="xs" dotColor="#ffffff" />
            <span>tensor frames</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-white" />
              <span>Valence {topMeta.valence}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full border border-white/70" />
              <span>Arousal {topMeta.arousal}</span>
            </span>
          </div>
        </div>

        {/* Center Spatial Visualizer: Tactile Dot Matrix or Trajectory Arcs */}
        <div className="my-5 py-2 flex items-center justify-center">
          <ArcTrajectoryGraph
            mode={visualMode}
            accentColor="#ffffff"
            className="w-full h-24 max-w-xs"
          />
        </div>

        {/* Bottom Big Dot-Matrix Number Display */}
        <div className="mt-2 border-t border-white/10 pt-4 flex items-end justify-between">
          <div>
            <span className="block font-mono text-[9px] uppercase tracking-wider text-white/60 mb-1">
              Calibrated Confidence Score
            </span>
            <div className="flex items-baseline gap-2">
              <DotMatrixNumber
                value={confidencePct}
                size="lg"
                dotColor="#ffffff"
                glowColor="rgba(255,255,255,0.4)"
              />
              <span className="font-mono text-sm font-bold text-white/90">%</span>
            </div>
          </div>

          <div className="text-right">
            <span className="font-mono text-[9px] text-white/50 block">Latency</span>
            <span className="font-mono text-xs font-semibold text-white/90">
              {(report.inference_time_sec * 1000).toFixed(0)} ms
            </span>
          </div>
        </div>
      </div>

      {/* 2. BEHAVIORAL TELEMETRY BENTO ROW (Minimal, subtle, tactile) */}
      <div className="grid grid-cols-2 gap-3.5">
        {/* Card A: Speaking Velocity */}
        <div className="rounded-[28px] squircle-obsidian p-5 border border-white/8">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-400">Speaking Velocity</span>
            <Waves className="h-3.5 w-3.5 text-slate-400" />
          </div>

          <div className="mt-2.5 flex items-baseline gap-1.5">
            <DotMatrixNumber
              value={behavior.speaking_speed.words_per_minute}
              size="sm"
              dotColor="#ffffff"
            />
            <span className="font-mono text-[10px] text-slate-400 uppercase">WPM</span>
          </div>

          <div className="mt-2 text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>{behavior.speaking_speed.syllables_per_second} syl/sec</span>
            <span className="text-white font-medium">{behavior.speaking_speed.category}</span>
          </div>

          {/* Minimal timeline indicator dots */}
          <div className="mt-3 flex items-center gap-1.5 pt-2 border-t border-white/6">
            {Array.from({ length: 9 }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1 rounded-full flex-1",
                  i < 6 ? "bg-white/70" : "bg-white/15",
                )}
              />
            ))}
          </div>
        </div>

        {/* Card B: Vocal Intensity (Radiant Ember Squircle) */}
        <div className="squircle-ember p-5 rounded-[28px] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-white/80">Vocal Energy</span>
            <Volume2 className="h-3.5 w-3.5 text-white/80" />
          </div>

          <div className="mt-2.5 flex items-baseline gap-1.5">
            <DotMatrixNumber
              value={Math.abs(behavior.vocal_energy.rms_db).toFixed(1)}
              size="sm"
              dotColor="#ffffff"
            />
            <span className="font-mono text-[10px] text-white/80 uppercase">dB RMS</span>
          </div>

          <div className="mt-2 text-[10px] text-white/70 font-mono flex items-center justify-between">
            <span>Dynamic Volume</span>
            <span className="text-white font-semibold">{behavior.vocal_energy.category}</span>
          </div>

          {/* Subtle arc trajectory graph */}
          <div className="mt-2 pt-1 border-t border-white/10 flex justify-center">
            <ArcTrajectoryGraph
              mode="arcs"
              accentColor="#ffffff"
              className="w-full h-8"
            />
          </div>
        </div>

        {/* Card C: Pause Ratio */}
        <div className="rounded-[28px] squircle-obsidian p-5 border border-white/8">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-400">Pause Cadence</span>
            <Zap className="h-3.5 w-3.5 text-slate-400" />
          </div>

          <div className="mt-2.5 flex items-baseline gap-1.5">
            <DotMatrixNumber
              value={behavior.pause_frequency.pauses_per_minute.toFixed(0)}
              size="sm"
              dotColor="#ffffff"
            />
            <span className="font-mono text-[10px] text-slate-400 uppercase">per min</span>
          </div>

          <div className="mt-2 text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>{behavior.pause_frequency.silence_ratio.toFixed(1)}% silence</span>
            <span className="text-white font-medium">{behavior.pause_frequency.category}</span>
          </div>

          {/* Minimal dot row */}
          <div className="mt-3 flex items-center gap-1 pt-2 border-t border-white/6">
            {Array.from({ length: 8 }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  i % 2 === 0 ? "bg-white" : "border border-white/30 bg-transparent",
                )}
              />
            ))}
          </div>
        </div>

        {/* Card D: Pitch F0 Contour */}
        <div className="rounded-[28px] squircle-obsidian p-5 border border-white/8">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-400">Pitch Contour</span>
            <Compass className="h-3.5 w-3.5 text-slate-400" />
          </div>

          <div className="mt-2.5 flex items-baseline gap-1.5">
            <DotMatrixNumber
              value={Math.round(behavior.pitch_variation.mean_hz)}
              size="sm"
              dotColor="#ffffff"
            />
            <span className="font-mono text-[10px] text-slate-400 uppercase">Hz F0</span>
          </div>

          <div className="mt-2 text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>±{Math.round(behavior.pitch_variation.std_hz)} Hz dev</span>
            <span className="text-white font-medium">{behavior.pitch_variation.category}</span>
          </div>

          <div className="mt-3 flex items-center justify-between pt-2 border-t border-white/6 text-[9px] font-mono text-slate-400">
            <span>Vocal Pitch</span>
            <span className="text-slate-300">pYIN Engine</span>
          </div>
        </div>
      </div>

      {/* 3. CALIBRATED PROBABILITY DISTRIBUTION (Minimal & Subtle) */}
      <div className="rounded-[28px] squircle-obsidian p-5 border border-white/8">
        <div className="flex items-center justify-between mb-3.5">
          <span className="text-xs font-semibold text-slate-300">
            Neural Probability Distribution
          </span>
          <button
            type="button"
            onClick={handleCopyJson}
            className="flex items-center gap-1 text-[10px] font-mono text-slate-400 hover:text-white transition-all"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Export JSON</span>
              </>
            )}
          </button>
        </div>

        <div className="space-y-2.5">
          {report.probabilities.map((item, idx) => {
            const meta = emotionMeta(item.emotion);
            const pct = (item.probability * 100).toFixed(1);
            const isWinner = item.emotion === report.predicted_emotion;

            return (
              <div
                key={item.emotion}
                className={cn(
                  "flex items-center justify-between rounded-xl px-3 py-2 transition-all",
                  isWinner ? "bg-white/6 border border-white/15" : "hover:bg-white/2",
                )}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      isWinner ? "bg-white shadow-[0_0_8px_#ffffff]" : "bg-white/25",
                    )}
                  />
                  <span className="truncate text-xs font-medium text-slate-200">
                    {meta.label}
                  </span>
                  <span className="font-mono text-[9px] text-slate-400">
                    {meta.tag}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className="hidden sm:block w-20 h-1 rounded-full bg-white/8 overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-300",
                        isWinner ? "bg-white" : "bg-white/40",
                      )}
                      style={{ width: `${Math.max(item.probability * 100, 3)}%` }}
                    />
                  </div>
                  <span className="font-mono text-xs font-semibold text-white min-w-[42px] text-right">
                    {pct}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
