"use client";

import { ChevronDown, Cpu, Loader2 } from "lucide-react";

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
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor="model-select" className={ui.label}>
          Emotion Classifier Model
        </label>
        {selected && (
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold",
              selected.checkpoint_available
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : "bg-slate-100 text-slate-600 border border-slate-200",
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                selected.checkpoint_available ? "bg-emerald-600" : "bg-slate-400",
              )}
            />
            {selected.checkpoint_available ? "Active" : "Untrained"}
          </span>
        )}
      </div>

      <div className="relative">
        {loading && (
          <Loader2 className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-slate-400" />
        )}
        <select
          id="model-select"
          value={value}
          disabled={loading || models.length === 0}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            ui.input,
            "cursor-pointer appearance-none pr-9 font-medium text-slate-900 bg-white",
          )}
        >
          {models.map((m) => (
            <option
              key={m.key}
              value={m.key}
              disabled={!m.checkpoint_available}
              className="text-slate-900"
            >
              {m.display_name} {m.checkpoint_available ? "" : "(Not loaded)"}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      </div>
    </div>
  );
}
