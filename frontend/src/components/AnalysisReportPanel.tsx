"use client";

import { Activity, Check, Copy, Loader2, Volume2 } from "lucide-react";
import { useState } from "react";

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

  const handleCopyJson = () => {
    if (!report) return;
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200/80 bg-white p-8 flex min-h-[380px] flex-col items-center justify-center text-center shadow-xs">
        <Loader2 className="h-8 w-8 animate-spin text-slate-800 mb-4" />
        <h3 className="text-sm font-semibold text-slate-900">
          Analyzing Speech Emotion
        </h3>
        <p className="mt-1 text-xs text-slate-500 max-w-xs leading-relaxed">
          Evaluating vocal pitch, rhythm, energy, and emotional probabilities...
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="rounded-2xl border border-slate-200/80 bg-white p-8 flex min-h-[380px] flex-col items-center justify-center text-center shadow-xs">
        <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
          <Activity className="h-6 w-6 stroke-[1.8]" />
        </div>
        <h3 className="text-sm font-semibold text-slate-900">
          No Speech Analyzed Yet
        </h3>
        <p className="mt-1 text-xs text-slate-500 max-w-xs leading-relaxed">
          Select a sample audio clip, upload a file, or record from your microphone to view emotion insights.
        </p>
      </div>
    );
  }

  const meta = emotionMeta(report.predicted_emotion);
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
    overall_behaviour: "Conversational Speaker",
  };

  return (
    <div className="space-y-4">
      {/* Primary Result Box */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Detected Emotion
            </span>
            <div className="flex items-center gap-3 mt-1.5">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                {meta.label}
              </h2>
              <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-semibold border", meta.badge)}>
                {confidencePct}% Confidence
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-600 leading-relaxed max-w-md">
              {meta.description}
            </p>
          </div>

          <button
            type="button"
            onClick={handleCopyJson}
            className="text-slate-400 hover:text-slate-700 text-xs font-medium flex items-center gap-1 transition-all"
            title="Copy JSON result"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>JSON</span>
              </>
            )}
          </button>
        </div>

        {/* Behavior Summary */}
        {report.summary && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 rounded-xl p-3 border border-slate-100">
              {report.summary}
            </p>
          </div>
        )}
      </div>

      {/* Emotion Probabilities Breakdown */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Emotion Probabilities
        </h4>

        <div className="space-y-2.5">
          {report.probabilities.map((item) => {
            const itemMeta = emotionMeta(item.emotion);
            const pct = (item.probability * 100).toFixed(1);
            const isWinner = item.emotion === report.predicted_emotion;

            return (
              <div key={item.emotion} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className={cn("font-medium", isWinner ? "text-slate-900 font-semibold" : "text-slate-600")}>
                    {itemMeta.label}
                  </span>
                  <span className={cn("font-medium", isWinner ? "text-slate-900 font-bold" : "text-slate-500")}>
                    {pct}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-300",
                      isWinner ? "bg-slate-900" : "bg-slate-300",
                    )}
                    style={{ width: `${Math.max(item.probability * 100, 1.5)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Acoustic & Speech Characteristics */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Speech Characteristics
        </h4>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Speaking Speed</span>
            <span className="text-sm font-bold text-slate-900">
              {behavior.speaking_speed.words_per_minute} WPM
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">
              {behavior.speaking_speed.syllables_per_second} syl/sec ({behavior.speaking_speed.category})
            </span>
          </div>

          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Pause Cadence</span>
            <span className="text-sm font-bold text-slate-900">
              {behavior.pause_frequency.pauses_per_minute.toFixed(0)} / min
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">
              {behavior.pause_frequency.silence_ratio.toFixed(0)}% silence ({behavior.pause_frequency.category})
            </span>
          </div>

          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Vocal Energy</span>
            <span className="text-sm font-bold text-slate-900">
              {behavior.vocal_energy.rms_db.toFixed(1)} dB
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">
              Volume: {behavior.vocal_energy.category}
            </span>
          </div>

          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Pitch (F0)</span>
            <span className="text-sm font-bold text-slate-900">
              {Math.round(behavior.pitch_variation.mean_hz)} Hz
            </span>
            <span className="text-[10px] text-slate-500 block mt-0.5">
              Variation: {behavior.pitch_variation.category}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
