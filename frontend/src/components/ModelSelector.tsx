"use client";

import { CheckCircle2, ChevronDown, Cpu, Layers, Loader2, Zap } from "lucide-react";

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
          <Cpu className="h-3.5 w-3.5 text-indigo-600" />
          Neural SER Backbone
        </label>
        {selected && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide",
              selected.checkpoint_available
                ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
                : "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
            )}
          >
            {selected.checkpoint_available ? (
              <>
                <CheckCircle2 className="h-2.5 w-2.5 text-emerald-600" />
                Checkpoint Loaded
              </>
            ) : (
              "Needs Weights"
            )}
          </span>
        )}
      </div>

      <div className="relative">
        {loading && (
          <Loader2 className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-slate-400" />
        )}
        <select
          id="model-select"
          value={value}
          disabled={loading || models.length === 0}
          onChange={(e) => onChange(e.target.value)}
          className={cn(ui.input, "cursor-pointer appearance-none pr-10 font-medium")}
        >
          {models.map((m) => (
            <option key={m.key} value={m.key} disabled={!m.checkpoint_available}>
              {m.display_name} {m.checkpoint_available ? "✓ (Ready)" : "(Untrained)"}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      </div>

      {selected && (
        <div className="flex flex-wrap items-center gap-2 pt-0.5">
          <div className="inline-flex items-center gap-1 rounded-lg border border-slate-200/90 bg-slate-50/80 px-2.5 py-1 text-[11px] font-medium text-slate-600">
            <Zap className="h-3 w-3 text-amber-500" />
            Input: <span className="font-semibold text-slate-800">{selected.input_type.toUpperCase()}</span>
          </div>

          <div className="inline-flex items-center gap-1 rounded-lg border border-slate-200/90 bg-slate-50/80 px-2.5 py-1 text-[11px] font-medium text-slate-600">
            <Layers className="h-3 w-3 text-indigo-500" />
            8-Class Multi-Logit
          </div>
        </div>
      )}
    </div>
  );
}
