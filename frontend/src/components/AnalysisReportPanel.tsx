"use client";

import {
  Activity,
  Award,
  BarChart3,
  Check,
  Clock,
  Copy,
  Cpu,
  Layers,
  Sparkles,
  Timer,
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
  { step: "1/4", label: "Decoding & Resampling Audio to 16 kHz Mono", pct: 25 },
  { step: "2/4", label: "Acoustic Feature & Temporal Latent Encoding", pct: 60 },
  { step: "3/4", label: "Multi-Head Attention & Logit Scoring", pct: 85 },
  { step: "4/4", label: "Calibrating Softmax Emotion Distribution", pct: 98 },
];

export function AnalysisReportPanel({ report, loading }: Props) {
  const [copied, setCopied] = useState(false);
  const [progressIdx, setProgressIdx] = useState(0);
  const [simulatedPct, setSimulatedPct] = useState(15);

  // Smooth animated multi-stage progress bar during inference
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
    }, 450);

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
      <div className={cn(ui.cardElevated, "flex min-h-[440px] flex-col items-center justify-center text-center")}>
        <div className="relative mb-6">
          <div className="absolute -inset-2 animate-ping rounded-full bg-indigo-500/20" />
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-[0_8px_25px_rgba(79,70,229,0.35)]">
            <Sparkles className="h-7 w-7 animate-pulse" />
          </div>
        </div>

        <h3 className="text-base font-semibold text-slate-900">Neural Inference Running</h3>
        <p className="mt-1 max-w-xs text-xs text-slate-500">{activeStep.label}</p>

        {/* Multi-step progress bar */}
        <div className="mt-6 w-full max-w-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-indigo-600">Step {activeStep.step}</span>
            <span className="font-mono text-slate-600">{simulatedPct}%</span>
          </div>
          <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-slate-200">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600 transition-all duration-500 ease-out"
              style={{ width: `${simulatedPct}%` }}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={cn(ui.cardMuted, "flex min-h-[440px] flex-col items-center justify-center border-dashed text-center")}>
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-200/90">
          <BarChart3 className="h-8 w-8 text-indigo-400" strokeWidth={1.5} />
        </div>
        <h3 className="text-base font-semibold text-slate-800">Intelligence Diagnostic Ready</h3>
        <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-slate-500">
          Select audio and trigger <span className="font-semibold text-indigo-600">Analyze Emotion</span> to view speech emotion confidence matrix and acoustic metrics.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {["8 Emotion Logits", "16kHz Resampling", "Softmax Calibration"].map((item) => (
            <span
              key={item}
              className="rounded-full border border-slate-200 bg-white/80 px-2.5 py-1 text-[10px] font-medium text-slate-500 shadow-2xs"
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

  return (
    <div className={cn(ui.cardElevated, "space-y-6 animate-in fade-in zoom-in-95 duration-300")}>
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">
            Acoustic Classification Report
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900">
            Emotion Diagnostic Summary
          </h2>
        </div>

        <button
          type="button"
          onClick={handleCopyJson}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-2xs transition-all hover:bg-slate-50 hover:text-slate-900"
          title="Copy raw JSON payload"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
          <span>{copied ? "Copied" : "JSON"}</span>
        </button>
      </div>

      {/* Hero Dominant Prediction Card */}
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl border p-5 transition-all",
          topMeta.borderColor,
          topMeta.lightBg,
        )}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-3xl shadow-sm ring-1 ring-slate-200">
              {topMeta.emoji}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-2xl font-bold text-slate-900">{topMeta.label}</h3>
                <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ring-1 ring-inset", topMeta.badge)}>
                  {topMeta.tag}
                </span>
              </div>
              <p className="mt-0.5 text-xs font-medium text-slate-500">
                Backbone: <span className="text-slate-800">{report.display_name}</span>
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-white/80 bg-white/90 px-4 py-2 text-right shadow-2xs backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Confidence</p>
            <p className="font-mono text-2xl font-bold tracking-tight text-indigo-600">
              {confidencePct}%
            </p>
          </div>
        </div>

        <p className="mt-3.5 rounded-xl border border-white/90 bg-white/80 p-3 text-xs leading-relaxed text-slate-600 shadow-2xs">
          {report.summary.replace(/\*\*/g, "")}
        </p>
      </div>

      {/* 4-Stat Diagnostic Grid */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <DiagnosticMetric
          icon={Timer}
          label="Inference"
          value={`${report.inference_time_sec.toFixed(3)}s`}
          accent="text-indigo-600"
        />
        <DiagnosticMetric
          icon={Clock}
          label="Audio Span"
          value={`${report.audio_duration_sec.toFixed(2)}s`}
          accent="text-teal-600"
        />
        <DiagnosticMetric
          icon={Activity}
          label="Rate"
          value={`${report.sample_rate / 1000} kHz`}
          accent="text-blue-600"
        />
        <DiagnosticMetric
          icon={Layers}
          label="Classes"
          value="8 Logits"
          accent="text-violet-600"
        />
      </div>

      {/* 8-Class Emotion Probability Spectrum */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
            <BarChart3 className="h-3.5 w-3.5 text-indigo-600" />
            Neural Probability Distribution
          </p>
          <span className="text-[11px] font-semibold text-slate-400">Softmax Calibrated</span>
        </div>

        <div className="space-y-2.5 rounded-2xl border border-slate-100 bg-slate-50/60 p-4">
          {report.probabilities.map((item, idx) => {
            const itemMeta = emotionMeta(item.emotion);
            const isWinner = item.emotion.toLowerCase() === report.predicted_emotion.toLowerCase();
            const pct = item.probability * 100;

            return (
              <div key={item.emotion} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-5 text-center text-sm">{itemMeta.emoji}</span>
                    <span className={cn("font-medium", isWinner ? "font-bold text-slate-900" : "text-slate-600")}>
                      {itemMeta.label}
                    </span>
                    {isWinner && (
                      <span className="inline-flex items-center gap-0.5 rounded-full bg-indigo-100 px-1.5 py-0.2 text-[9px] font-bold text-indigo-700">
                        <Award className="h-2.5 w-2.5" />
                        Top
                      </span>
                    )}
                  </div>

                  <span className={cn("font-mono font-semibold tabular-nums", isWinner ? "text-indigo-600 font-bold" : "text-slate-500")}>
                    {pct.toFixed(1)}%
                  </span>
                </div>

                <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-200/80">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-700 ease-out",
                      isWinner ? "bg-gradient-to-r from-indigo-500 to-violet-600 shadow-[0_0_8px_rgba(99,102,241,0.5)]" : "bg-gradient-to-r from-slate-400 to-slate-500",
                    )}
                    style={{ width: `${Math.max(pct, 1.5)}%` }}
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

function DiagnosticMetric({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof Timer;
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs transition-all hover:border-slate-300">
      <div className="flex items-center gap-1.5 text-slate-400">
        <Icon className={cn("h-3.5 w-3.5", accent)} />
        <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
      </div>
      <p className="mt-1 font-mono text-sm font-bold text-slate-800">{value}</p>
    </div>
  );
}
