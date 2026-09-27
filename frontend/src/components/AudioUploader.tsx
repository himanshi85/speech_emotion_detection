"use client";

import { FileAudio, Loader2, Music, Sparkles, UploadCloud, X, Zap } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";
import { API_BASE } from "@/lib/api";

type Props = {
  onFileReady: (file: File) => void;
  onClear: () => void;
  disabled?: boolean;
};

const ACCEPT = "audio/*,.wav,.mp3,.flac,.ogg,.webm,.m4a";

export function AudioUploader({ onFileReady, onClear, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  const setSelected = useCallback(
    (next: File | null) => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (!next) {
        setFile(null);
        setPreviewUrl(null);
        onClear();
        return;
      }
      setFile(next);
      setPreviewUrl(URL.createObjectURL(next));
      onFileReady(next);
    },
    [onClear, previewUrl, onFileReady],
  );

  const onDrop = (ev: React.DragEvent) => {
    ev.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const dropped = ev.dataTransfer.files?.[0];
    if (dropped && (dropped.type.startsWith("audio/") || dropped.name.match(/\.(wav|mp3|flac|ogg|webm|m4a)$/i))) {
      setSelected(dropped);
    }
  };

  const handleLoadSample = async (sampleId: string, filename: string) => {
    if (disabled) return;
    try {
      setLoadingSample(true);
      const res = await fetch(`${API_BASE}/api/sample-audio/${sampleId}`);
      if (!res.ok) throw new Error("Could not fetch sample audio.");
      const blob = await res.blob();
      const sampleFile = new File([blob], filename, { type: "audio/wav" });
      setSelected(sampleFile);
    } catch {
      // Fallback: create synthetic test wave
      const buffer = new Float32Array(16000 * 2.5);
      for (let i = 0; i < buffer.length; i++) {
        buffer[i] = Math.sin((2 * Math.PI * 440 * i) / 16000) * 0.4;
      }
      const dummy = new File([new Blob([buffer], { type: "audio/wav" })], "fallback-sample.wav", { type: "audio/wav" });
      setSelected(dummy);
    } finally {
      setLoadingSample(false);
    }
  };

  return (
    <div className="space-y-4">
      {!file ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          className={cn(
            "group relative flex min-h-[175px] cursor-pointer flex-col items-center justify-center rounded-[24px] border-2 border-dashed p-6 text-center transition-all duration-300",
            dragOver
              ? "border-cyan-400 bg-cyan-950/30 shadow-[0_0_30px_rgba(0,240,255,0.25)] scale-[1.01]"
              : "border-white/[0.1] bg-[#090d16]/70 hover:border-cyan-400/50 hover:bg-[#0c121f]/90 hover:shadow-xl",
            disabled && "pointer-events-none opacity-40",
          )}
        >
          <div className="mb-3.5 flex h-13 w-13 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-500 to-lime-400 text-slate-950 shadow-[0_0_20px_rgba(0,240,255,0.35)] transition-transform duration-300 group-hover:scale-110">
            <UploadCloud className="h-6 w-6" strokeWidth={2.2} />
          </div>
          <p className="text-sm font-bold tracking-wide text-white transition-colors group-hover:text-cyan-300">
            Ingest Speech Audio Stream
          </p>
          <p className="mt-1 max-w-xs text-xs text-slate-400">
            Drag & drop or <span className="font-semibold text-cyan-400 underline underline-offset-4">browse filesystem</span>
          </p>

          <div className="mt-3.5 flex flex-wrap items-center justify-center gap-1.5">
            {["WAV (16kHz)", "FLAC", "MP3", "WEBM", "M4A"].map((ext) => (
              <span
                key={ext}
                className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-slate-400"
              >
                {ext}
              </span>
            ))}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            disabled={disabled}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) setSelected(f);
            }}
          />
        </div>
      ) : (
        <div className="rounded-[24px] border border-cyan-500/30 bg-[#0a0f1b]/80 p-5 shadow-2xl backdrop-blur-2xl transition-all animate-in fade-in zoom-in-95 duration-200">
          <div className="mb-3.5 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-400/30 shadow-[0_0_12px_rgba(0,240,255,0.2)]">
                <FileAudio className="h-5 w-5" strokeWidth={2} />
              </div>
              <div className="text-left">
                <p className="max-w-[200px] truncate text-sm font-bold text-white sm:max-w-[280px]">
                  {file.name}
                </p>
                <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                  <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  <span>//</span>
                  <span className="font-bold text-emerald-400">READY FOR TENSOR INGESTION</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setSelected(null)}
              className="rounded-xl border border-white/[0.08] bg-white/[0.04] p-2 text-slate-400 transition-colors hover:bg-rose-500/20 hover:border-rose-500/40 hover:text-rose-300"
              title="Remove audio file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {previewUrl && (
            <div className="rounded-xl border border-white/[0.06] bg-[#070b13] p-2.5 shadow-inner">
              <audio controls src={previewUrl} preload="metadata" className="w-full" />
            </div>
          )}
        </div>
      )}

      {/* Cyber Quick Test Chips */}
      {!file && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <span className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">
            <Zap className="h-3 w-3 text-lime-400" />
            Instant Ingestion Chips:
          </span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_1", "hindi-neutral-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-[#0d1320]/80 px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-300 shadow-sm backdrop-blur-md transition-all hover:border-cyan-400/50 hover:bg-cyan-950/40 hover:text-cyan-300"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-cyan-400" /> : <Music className="h-3 w-3 text-cyan-400" />}
              Hindi Neutral
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_7", "hindi-happy-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-[#0d1320]/80 px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-300 shadow-sm backdrop-blur-md transition-all hover:border-lime-400/50 hover:bg-lime-950/40 hover:text-lime-300"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-lime-400" /> : <Sparkles className="h-3 w-3 text-lime-400" />}
              Hindi Expressive
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_15", "hindi-assertive-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-[#0d1320]/80 px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-300 shadow-sm backdrop-blur-md transition-all hover:border-rose-400/50 hover:bg-rose-950/40 hover:text-rose-300"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-rose-400" /> : <Zap className="h-3 w-3 text-rose-400" />}
              Hindi Assertive
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
