"use client";

import { FileAudio, Loader2, Play, UploadCloud, Volume2, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { AudioWaveformVisualizer } from "@/components/AudioWaveformVisualizer";
import { API_BASE } from "@/lib/api";

type Props = {
  onFileReady: (file: File) => void;
  onClear: () => void;
  disabled?: boolean;
};

const ACCEPT = "audio/*,.wav,.mp3,.flac,.ogg,.webm,.m4a";

export function AudioUploader({ onFileReady, onClear, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loadingSample, setLoadingSample] = useState(false);

  const setSelected = useCallback(
    (next: File | null) => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (!next) {
        setFile(null);
        setPreviewUrl(null);
        setIsPlaying(false);
        onClear();
        return;
      }
      setFile(next);
      setPreviewUrl(URL.createObjectURL(next));
      setIsPlaying(false);
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
      const dummy = new File([new Blob([buffer], { type: "audio/wav" })], "sample.wav", { type: "audio/wav" });
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
          className={`flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition-all ${
            dragOver
              ? "border-slate-900 bg-slate-100/60"
              : "border-slate-200 bg-slate-50/50 hover:border-slate-400 hover:bg-slate-50"
          } ${disabled ? "pointer-events-none opacity-50" : ""}`}
        >
          <div className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-700 shadow-xs border border-slate-200">
            <UploadCloud className="h-5 w-5" />
          </div>
          <p className="text-xs font-semibold text-slate-800">
            Click to upload or drag audio file here
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            Supports WAV, MP3, FLAC, WEBM (16 kHz recommended)
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
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 border border-slate-200">
                <FileAudio className="h-4 w-4" />
              </div>
              <div className="truncate">
                <p className="truncate text-xs font-semibold text-slate-900">
                  {file.name}
                </p>
                <p className="text-[11px] text-slate-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB • Audio Ready
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setSelected(null)}
              className="h-8 w-8 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition-all"
              title="Remove file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Smooth Real-Time Waveform Visualizer */}
          <AudioWaveformVisualizer
            audioRef={audioRef}
            isPlaying={isPlaying}
            className="w-full h-16"
          />

          {previewUrl && (
            <div className="pt-1">
              <audio
                ref={audioRef}
                controls
                src={previewUrl}
                preload="metadata"
                className="w-full h-9"
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onEnded={() => setIsPlaying(false)}
              />
            </div>
          )}
        </div>
      )}

      {/* Benchmark Audio Samples */}
      {!file && (
        <div className="space-y-2 pt-1">
          <span className="text-[11px] font-medium text-slate-500 block">
            Or test with sample speech recordings:
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_1", "hindi-neutral-sample.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-2xs hover:bg-slate-50 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Volume2 className="h-3.5 w-3.5 text-slate-400" />}
              Sample 1 (Neutral)
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_7", "hindi-happy-sample.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-2xs hover:bg-slate-50 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Volume2 className="h-3.5 w-3.5 text-slate-400" />}
              Sample 2 (Happy)
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample("hindi_15", "hindi-assertive-sample.wav")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-2xs hover:bg-slate-50 transition-all"
            >
              {loadingSample ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Volume2 className="h-3.5 w-3.5 text-slate-400" />}
              Sample 3 (Angry)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
