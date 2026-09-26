"use client";

import { FileAudio, Music, Sparkles, UploadCloud, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";

type Props = {
  onFileReady: (file: File) => void;
  onClear: () => void;
  disabled?: boolean;
};

const ACCEPT = "audio/*,.wav,.mp3,.flac,.ogg,.webm,.m4a";

// Sample generator for instant 1-click test drive
function createSampleAudioBlob(frequency: number, type: "sine" | "sawtooth" | "triangle"): Promise<File> {
  return new Promise((resolve) => {
    const sampleRate = 16000;
    const duration = 2.5;
    const numSamples = Math.floor(sampleRate * duration);
    const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)({
      sampleRate,
    });
    
    const buffer = audioContext.createBuffer(1, numSamples, sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < numSamples; i++) {
      const t = i / sampleRate;
      const envelope = Math.sin((Math.PI * t) / duration); // Smooth bell curve envelope
      if (type === "sine") {
        data[i] = envelope * Math.sin(2 * Math.PI * frequency * t);
      } else if (type === "sawtooth") {
        data[i] = envelope * (2 * (t * frequency - Math.floor(t * frequency + 0.5)));
      } else {
        data[i] = envelope * Math.asin(Math.sin(2 * Math.PI * frequency * t)) * (2 / Math.PI);
      }
    }
    
    // Convert AudioBuffer to WAV blob
    const wavBlob = audioBufferToWavBlob(buffer);
    const sampleFile = new File([wavBlob], `sample-${type}-${Math.round(frequency)}hz.wav`, {
      type: "audio/wav",
    });
    resolve(sampleFile);
  });
}

function audioBufferToWavBlob(buffer: AudioBuffer): Blob {
  const numOfChan = buffer.numberOfChannels;
  const length = buffer.length * numOfChan * 2 + 44;
  const out = new DataView(new ArrayBuffer(length));
  const channels: Float32Array[] = [];
  let sampleRate = buffer.sampleRate;
  let offset = 0;
  let pos = 0;

  function setUint16(data: number) {
    out.setUint16(pos, data, true);
    pos += 2;
  }

  function setUint32(data: number) {
    out.setUint32(pos, data, true);
    pos += 4;
  }

  // RIFF header
  out.setUint32(pos, 0x46464952, false); // "RIFF"
  pos += 4;
  setUint32(length - 8);
  out.setUint32(pos, 0x45564157, false); // "WAVE"
  pos += 4;

  // FMT sub-chunk
  out.setUint32(pos, 0x20746d66, false); // "fmt "
  pos += 4;
  setUint32(16); // subChunk1Size
  setUint16(1); // PCM
  setUint16(numOfChan);
  setUint32(sampleRate);
  setUint32(sampleRate * 2 * numOfChan); // byte rate
  setUint16(numOfChan * 2); // block align
  setUint16(16); // bits per sample

  // Data sub-chunk
  out.setUint32(pos, 0x61746164, false); // "data"
  pos += 4;
  setUint32(length - pos - 4);

  for (let i = 0; i < buffer.numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i));
  }

  while (offset < buffer.length) {
    for (let i = 0; i < numOfChan; i++) {
      let sample = Math.max(-1, Math.min(1, channels[i][offset]));
      sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
      out.setInt16(pos, sample, true);
      pos += 2;
    }
    offset++;
  }

  return new Blob([out.buffer], { type: "audio/wav" });
}

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

  const handleLoadSample = async (freq: number, type: "sine" | "sawtooth" | "triangle") => {
    if (disabled) return;
    try {
      setLoadingSample(true);
      const sampleFile = await createSampleAudioBlob(freq, type);
      setSelected(sampleFile);
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
            "group relative flex min-h-[175px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition-all duration-300",
            dragOver
              ? "border-indigo-500 bg-indigo-50/60 shadow-[0_0_24px_rgba(99,102,241,0.2)] scale-[1.01]"
              : "border-slate-300/90 bg-gradient-to-b from-slate-50/70 to-white hover:border-indigo-400/80 hover:bg-indigo-50/20 hover:shadow-sm",
            disabled && "pointer-events-none opacity-50",
          )}
        >
          <div className="mb-3.5 flex h-13 w-13 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-[0_6px_16px_rgba(79,70,229,0.25)] transition-transform duration-300 group-hover:scale-105 group-hover:shadow-[0_8px_20px_rgba(79,70,229,0.35)]">
            <UploadCloud className="h-6 w-6" strokeWidth={2} />
          </div>
          <p className="text-sm font-semibold text-slate-800 transition-colors group-hover:text-indigo-600">
            Upload speech audio file
          </p>
          <p className="mt-1 max-w-xs text-xs text-slate-500">
            Drag & drop or <span className="font-semibold text-indigo-600 underline underline-offset-2">browse</span> from device
          </p>
          
          <div className="mt-3 flex flex-wrap items-center justify-center gap-1.5">
            {["WAV", "MP3", "FLAC", "WEBM", "M4A"].map((ext) => (
              <span
                key={ext}
                className="rounded-md border border-slate-200/80 bg-white px-2 py-0.5 text-[10px] font-medium text-slate-500 shadow-2xs"
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
        <div className="rounded-2xl border border-indigo-100 bg-gradient-to-b from-indigo-50/40 via-white to-white p-4 shadow-sm transition-all animate-in fade-in zoom-in-95 duration-200">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
                <FileAudio className="h-5 w-5" strokeWidth={2} />
              </div>
              <div className="text-left">
                <p className="max-w-[220px] truncate text-sm font-semibold text-slate-900 sm:max-w-[280px]">
                  {file.name}
                </p>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  <span>•</span>
                  <span className="font-medium text-emerald-600">Ready for model</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setSelected(null)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
              title="Remove audio file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {previewUrl && (
            <div className="rounded-xl border border-slate-200/70 bg-white p-2.5 shadow-2xs">
              <audio controls src={previewUrl} preload="metadata" className="w-full" />
            </div>
          )}
        </div>
      )}

      {/* Quick sample audio presets */}
      {!file && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-0.5">
          <span className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400">
            <Sparkles className="h-3 w-3 text-indigo-500" />
            Try test samples:
          </span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample(440, "sine")}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 shadow-2xs transition-all hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700"
            >
              <Music className="h-3 w-3 text-indigo-500" />
              Sample A (440Hz)
            </button>
            <button
              type="button"
              disabled={disabled || loadingSample}
              onClick={() => handleLoadSample(880, "sawtooth")}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 shadow-2xs transition-all hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700"
            >
              <Music className="h-3 w-3 text-amber-500" />
              Sample B (880Hz)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
