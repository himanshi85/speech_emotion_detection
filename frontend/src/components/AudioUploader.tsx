"use client";

import { FileAudio, Loader2, Music, UploadCloud, X, Zap } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { cn } from "@/lib/cn";
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
    <div className="space-y-3.5">
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
            "group relative flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed p-6 text-center transition-all duration-300",
            dragOver
              ? "border-white bg-white/10 shadow-[0_0_24px_rgba(255,255,255,0.2)] scale-[1.01]"
              : "border-white/12 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.04]",
            disabled && "pointer-events-none opacity-40",
          )}
        >
          <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-white text-black shadow-md transition-transform duration-300 group-hover:scale-105">
            <UploadCloud className="h-5 w-5 stroke-[2]" />
          </div>
          <p className="text-xs font-semibold text-white tracking-wide">
            Select or drop speech audio
          </p>
          <p className="mt-1 text-[11px] text-slate-400">
            WAV 16 kHz recommended, FLAC, MP3, M4A supported
          </p>

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
        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/10 text-white border border-white/15">
                <FileAudio className="h-4 w-4" />
              </div>
              <div className="truncate">
                <p className="truncate text-xs font-semibold text-white">
                  {file.name}
                </p>
                <p className="font-mono text-[10px] text-slate-400">
                  {(file.size / 1024 / 1024).toFixed(2)} MB • Audio Loaded
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setSelected(null)}
              className="h-8 w-8 rounded-full bg-white/6 hover:bg-white/12 text-slate-300 hover:text-white flex items-center justify-center transition-all border border-white/10"
              title="Remove audio file"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {previewUrl && (
            <div className="rounded-xl border border-white/6 bg-black/40 p-2">
              <audio controls src={previewUrl} preload="metadata" className="w-full h-8" />
            </div>
          )}
        </div>
      )}

      {/* Subtle Benchmark Audio Pills */}
      {!file && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400">
            Benchmark Samples:
          </span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_1", "hindi-neutral-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 font-mono text-[10px] text-slate-300 hover:text-white hover:bg-white/10 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-white" /> : <Music className="h-3 w-3 text-slate-400" />}
              Hindi #1 Neutral
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_7", "hindi-happy-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 font-mono text-[10px] text-slate-300 hover:text-white hover:bg-white/10 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-white" /> : <Zap className="h-3 w-3 text-slate-400" />}
              Hindi #2 Expressive
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_15", "hindi-assertive-speech.wav")}
              className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 font-mono text-[10px] text-slate-300 hover:text-white hover:bg-white/10 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3 w-3 animate-spin text-white" /> : <Zap className="h-3 w-3 text-slate-400" />}
              Hindi #3 Assertive
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
