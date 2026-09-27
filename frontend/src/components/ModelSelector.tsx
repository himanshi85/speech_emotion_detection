"use client";

import { ChevronDown, Cpu, Layers, Loader2, Sparkles, Zap } from "lucide-react";

import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";
import type { ModelInfo } from "@/types/analysis";

type Props = {
  models: ModelInfo[];
  value: string;
  onChange: (key: string) => void;
  loading?: boolean;
};

export function ModelSelector({ models, value, onChange, loading }: Props) {
  const selected = models.find((m) => m.key === value) ?? models[0];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label htmlFor="model-select" className={cn(ui.label, "flex items-center gap-1.5")}>
          <Cpu className="h-3.5 w-3.5 text-cyan-400" />
          Neural Backbone Architecture
        </label>
        {selected && (
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-wide uppercase",
              selected.checkpoint_available
                ? "border border-emerald-500/40 bg-emerald-950/50 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.25)]"
                : "border border-amber-500/40 bg-amber-950/50 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.25)]",
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                selected.checkpoint_available
                  ? "bg-emerald-400 shadow-[0_0_6px_#10b981]"
                  : "bg-amber-400",
              )}
            />
            {selected.checkpoint_available ? "Weights Loaded" : "Awaiting Weights"}
          </span>
        )}
      </div>

      <div className="relative">
        {loading && (
          <Loader2 className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-cyan-400" />
        )}
        <select
          id="model-select"
          value={value}
          disabled={loading || models.length === 0}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            ui.input,
            "cursor-pointer appearance-none pr-10 font-semibold tracking-wide text-slate-100",
          )}
        >
          {models.map((m) => (
            <option
              key={m.key}
              value={m.key}
              disabled={!m.checkpoint_available}
              className="bg-[#0b0f18] text-slate-200"
            >
              {m.display_name} {m.checkpoint_available ? "[READY]" : "[UNTRAINED]"}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      </div>

      {selected && (
        <div className="flex flex-wrap items-center gap-2 pt-0.5">
          <div className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-300 backdrop-blur-md">
            <Zap className="h-3 w-3 text-lime-400" />
            Input: <span className="font-bold text-white">{selected.input_type}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-300 backdrop-blur-md">
            <Layers className="h-3 w-3 text-cyan-400" />
            Tensor: <span className="text-slate-300 truncate max-w-[200px]">{selected.architecture.split("->")[0]}</span>
          </div>
        </div>
      )}
    </div>
  );
}
