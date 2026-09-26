"use client";

import { Mic, Pause, Play, RotateCcw, Sparkles, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { ui } from "@/lib/ui";

type Props = {
  onRecordingReady: (blob: Blob, filename: string) => void;
  onClear: () => void;
  disabled?: boolean;
};

function formatTime(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  const ms = Math.floor((totalSeconds % 1) * 10);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${ms}`;
}

export function AudioRecorder({ onRecordingReady, onClear, disabled }: Props) {
  const [status, setStatus] = useState<"idle" | "recording" | "paused">("idle");
  const [elapsed, setElapsed] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);

  const stopVisualizer = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const drawVisualizer = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const buffer = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(buffer);
      const { width, height } = canvas;
      
      // Clean canvas background
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);

      // Subtle horizontal center baseline
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      const numBars = 36;
      const barWidth = width / numBars - 2.5;
      const step = Math.floor(buffer.length / numBars);

      for (let i = 0; i < numBars; i++) {
        const val = buffer[i * step] / 255;
        const barHeight = Math.max(val * (height * 0.8), 4);
        const x = i * (barWidth + 2.5) + 2;
        const y = (height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        if (status === "recording") {
          gradient.addColorStop(0, "#4f46e5");
          gradient.addColorStop(0.5, "#6366f1");
          gradient.addColorStop(1, "#818cf8");
        } else {
          gradient.addColorStop(0, "#94a3b8");
          gradient.addColorStop(1, "#cbd5e1");
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    draw();
  }, [status]);

  const cleanupStream = useCallback(() => {
    stopVisualizer();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    analyserRef.current = null;
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [stopVisualizer]);

  useEffect(() => {
    return () => {
      cleanupStream();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [cleanupStream, previewUrl]);

  const startTimer = (offset = 0) => {
    startTimeRef.current = Date.now() - offset * 1000;
    timerRef.current = window.setInterval(() => {
      setElapsed((Date.now() - startTimeRef.current) / 1000);
    }, 100);
  };

  const startRecording = async () => {
    setError(null);
    onClear();
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;
      drawVisualizer();

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunksRef.current.push(ev.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        onRecordingReady(blob, `recording-${Date.now()}.webm`);
        cleanupStream();
        setStatus("idle");
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250);
      setElapsed(0);
      setStatus("recording");
      startTimer(0);
    } catch {
      setError("Microphone access was denied or not supported by this browser.");
    }
  };

  const pauseRecording = () => {
    const rec = mediaRecorderRef.current;
    if (!rec || rec.state !== "recording") return;
    rec.pause();
    pausedTimeRef.current = elapsed;
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    stopVisualizer();
    setStatus("paused");
  };

  const resumeRecording = () => {
    const rec = mediaRecorderRef.current;
    if (!rec || rec.state !== "paused") return;
    rec.resume();
    startTimer(pausedTimeRef.current);
    drawVisualizer();
    setStatus("recording");
  };

  const stopRecording = () => {
    const rec = mediaRecorderRef.current;
    if (!rec || rec.state === "inactive") return;
    rec.stop();
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const discard = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    cleanupStream();
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setElapsed(0);
    setStatus("idle");
    onClear();
  };

  return (
    <div className="space-y-4">
      {/* Visualizer & Timer Display Card */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-2.5 w-2.5 rounded-full transition-all",
                status === "recording" && "bg-rose-500 pulse-ring-active",
                status === "paused" && "bg-amber-500",
                status === "idle" && "bg-slate-300",
              )}
            />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
              {status === "recording" && "Live Recording Audio"}
              {status === "paused" && "Recording Paused"}
              {status === "idle" && (previewUrl ? "Recording Complete" : "Mic Input Ready")}
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-sm font-semibold tracking-wide text-indigo-600">
            {formatTime(elapsed)}
          </div>
        </div>

        <div className="py-3">
          <canvas ref={canvasRef} width={520} height={70} className="h-16 w-full rounded-lg" />
        </div>

        {/* Action button controls */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {status === "idle" && !previewUrl && (
            <button
              type="button"
              disabled={disabled}
              onClick={startRecording}
              className={cn(ui.btnPrimary, "w-full sm:w-auto")}
            >
              <Mic className="h-4 w-4" />
              Start Recording
            </button>
          )}

          {status === "recording" && (
            <>
              <button type="button" onClick={pauseRecording} className={ui.btnWarning}>
                <Pause className="h-4 w-4" />
                Pause
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnDanger}>
                <Square className="h-4 w-4 fill-current" />
                Stop & Process
              </button>
            </>
          )}

          {status === "paused" && (
            <>
              <button type="button" onClick={resumeRecording} className={ui.btnSuccess}>
                <Play className="h-4 w-4" />
                Resume
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnDanger}>
                <Square className="h-4 w-4 fill-current" />
                Stop & Process
              </button>
            </>
          )}

          {previewUrl && status === "idle" && (
            <button type="button" onClick={discard} className={ui.btnSecondary}>
              <RotateCcw className="h-4 w-4" />
              Re-record
            </button>
          )}
        </div>
      </div>

      {previewUrl && status === "idle" && (
        <div className="rounded-2xl border border-indigo-100 bg-gradient-to-b from-indigo-50/40 via-white to-white p-4 shadow-sm animate-in fade-in zoom-in-95 duration-200">
          <div className="mb-2.5 flex items-center justify-between text-xs font-semibold text-slate-700">
            <span className="flex items-center gap-1.5 text-indigo-700">
              <Sparkles className="h-3.5 w-3.5" />
              Captured Audio Clip
            </span>
            <span className="font-mono text-slate-500">{formatTime(elapsed)}</span>
          </div>
          <audio controls src={previewUrl} preload="metadata" className="w-full" />
        </div>
      )}

      {error && (
        <div className={ui.alertError}>
          <p className="font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
