"use client";

import { Mic, Pause, Play, RotateCcw, Square, Volume2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { AudioWaveformVisualizer } from "@/components/AudioWaveformVisualizer";
import { ui } from "@/lib/ui";

type Props = {
  onRecordingReady: (blob: Blob, filename: string) => void;
  onClear: () => void;
  disabled?: boolean;
};

function formatTime(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function AudioRecorder({ onRecordingReady, onClear, disabled }: Props) {
  const [status, setStatus] = useState<"idle" | "recording" | "paused">("idle");
  const [elapsed, setElapsed] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);

  const cleanupStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      setStream(null);
    }
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [stream]);

  useEffect(() => {
    return () => {
      cleanupStream();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [cleanupStream, previewUrl]);

  const startRecording = async () => {
    if (disabled) return;
    setError(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    chunksRef.current = [];

    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      setStream(audioStream);

      const mimeType = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
      ].find((t) => MediaRecorder.isTypeSupported(t)) || "";

      const mr = new MediaRecorder(audioStream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mr;

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const type = mr.mimeType || "audio/webm";
        const ext = type.includes("ogg") ? "ogg" : type.includes("mp4") ? "mp4" : "webm";
        const blob = new Blob(chunksRef.current, { type });
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        onRecordingReady(blob, `recording-${Date.now()}.${ext}`);
        cleanupStream();
      };

      mr.start(250);
      startTimeRef.current = Date.now();
      setStatus("recording");

      timerRef.current = window.setInterval(() => {
        setElapsed((Date.now() - startTimeRef.current) / 1000);
      }, 100);
    } catch (err) {
      cleanupStream();
      setStatus("idle");
      setError(err instanceof Error ? err.message : "Microphone permission required.");
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && status === "recording") {
      mediaRecorderRef.current.pause();
      pausedTimeRef.current = Date.now();
      if (timerRef.current) window.clearInterval(timerRef.current);
      setStatus("paused");
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && status === "paused") {
      mediaRecorderRef.current.resume();
      startTimeRef.current += Date.now() - pausedTimeRef.current;
      setStatus("recording");
      timerRef.current = window.setInterval(() => {
        setElapsed((Date.now() - startTimeRef.current) / 1000);
      }, 100);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && (status === "recording" || status === "paused")) {
      mediaRecorderRef.current.stop();
      setStatus("idle");
    }
  };

  const discard = () => {
    cleanupStream();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setElapsed(0);
    setStatus("idle");
    onClear();
  };

  return (
    <div className="space-y-4">
      {/* Live Waveform & Timer Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                status === "recording"
                  ? "bg-rose-500 animate-pulse"
                  : status === "paused"
                  ? "bg-amber-400"
                  : "bg-slate-300"
              }`}
            />
            <span className="text-xs font-medium text-slate-600">
              {status === "recording" && "Recording in progress"}
              {status === "paused" && "Recording paused"}
              {status === "idle" && (previewUrl ? "Recording complete" : "Microphone ready")}
            </span>
          </div>

          <span className="font-mono text-xs font-semibold text-slate-900">
            {formatTime(elapsed)}
          </span>
        </div>

        {/* Live Audio Frequency Waveform Visualizer */}
        <AudioWaveformVisualizer
          stream={stream}
          isRecording={status === "recording"}
          className="w-full h-18"
        />

        {/* Controls */}
        <div className="flex items-center justify-center gap-2.5 pt-1">
          {status === "idle" && !previewUrl && (
            <button
              type="button"
              disabled={disabled}
              onClick={startRecording}
              className={ui.btnPrimary}
            >
              <Mic className="h-4 w-4" />
              <span>Start Recording</span>
            </button>
          )}

          {status === "recording" && (
            <>
              <button type="button" onClick={pauseRecording} className={ui.btnSecondary}>
                <Pause className="h-4 w-4" />
                <span>Pause</span>
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnPrimary}>
                <Square className="h-4 w-4 fill-white" />
                <span>Stop & Use</span>
              </button>
            </>
          )}

          {status === "paused" && (
            <>
              <button type="button" onClick={resumeRecording} className={ui.btnSecondary}>
                <Play className="h-4 w-4" />
                <span>Resume</span>
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnPrimary}>
                <Square className="h-4 w-4 fill-white" />
                <span>Stop & Use</span>
              </button>
            </>
          )}

          {previewUrl && status === "idle" && (
            <button type="button" onClick={discard} className={ui.btnSecondary}>
              <RotateCcw className="h-4 w-4" />
              <span>Record Again</span>
            </button>
          )}
        </div>
      </div>

      {previewUrl && status === "idle" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-xs">
          <div className="mb-2 flex items-center justify-between text-xs text-slate-700">
            <span className="flex items-center gap-1.5 font-medium">
              <Volume2 className="h-3.5 w-3.5 text-slate-400" />
              Recorded Speech Clip
            </span>
            <span className="font-mono text-slate-500">{formatTime(elapsed)}</span>
          </div>
          <audio controls src={previewUrl} preload="metadata" className="w-full h-9" />
        </div>
      )}

      {error && (
        <div className={ui.alertError}>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
