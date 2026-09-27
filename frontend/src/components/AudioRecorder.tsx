"use client";

import { Mic, Pause, Play, RotateCcw, Sparkles, Square, Volume2 } from "lucide-react";
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

      // Dark cyber-glass canvas background
      ctx.fillStyle = "#070b13";
      ctx.fillRect(0, 0, width, height);

      // Subtle horizontal center baseline
      ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      const numBars = 42;
      const barWidth = width / numBars - 3;
      const step = Math.floor(buffer.length / numBars);

      for (let i = 0; i < numBars; i++) {
        const val = buffer[i * step] / 255;
        const barHeight = Math.max(val * (height * 0.85), 3);
        const x = i * (barWidth + 3) + 2;
        const y = (height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        if (status === "recording") {
          gradient.addColorStop(0, "#00f0ff");
          gradient.addColorStop(0.5, "#00f59b");
          gradient.addColorStop(1, "#ccff00");
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 6;
        } else {
          gradient.addColorStop(0, "rgba(148, 163, 184, 0.3)");
          gradient.addColorStop(1, "rgba(203, 213, 225, 0.1)");
          ctx.shadowBlur = 0;
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
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    analyserRef.current = null;
  }, [stopVisualizer]);

  useEffect(() => {
    return () => {
      cleanupStream();
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [cleanupStream]);

  const startTimer = (baseElapsed: number) => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    startTimeRef.current = performance.now();
    timerRef.current = window.setInterval(() => {
      const now = performance.now();
      const currentSpan = (now - startTimeRef.current) / 1000;
      setElapsed(baseElapsed + currentSpan);
    }, 100);
  };

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const audioCtx = new (window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 128;
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
      <div className="relative overflow-hidden rounded-[24px] border border-white/[0.08] bg-[#090d16]/70 p-5 shadow-2xl backdrop-blur-2xl">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-2 w-2 rounded-full transition-all",
                status === "recording" && "bg-rose-500 shadow-[0_0_8px_#f43f5e] animate-pulse",
                status === "paused" && "bg-amber-400 shadow-[0_0_8px_#fbbf24]",
                status === "idle" && "bg-slate-600",
              )}
            />
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">
              {status === "recording" && "LIVE AUDIO CAPTURE // ACTIVE"}
              {status === "paused" && "BUFFER PAUSED"}
              {status === "idle" && (previewUrl ? "SAMPLING READY" : "AUDIO SENSOR STANDBY")}
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-sm font-bold tracking-wider text-cyan-400">
            {formatTime(elapsed)}
          </div>
        </div>

        <div className="py-3">
          <canvas ref={canvasRef} width={520} height={70} className="h-16 w-full rounded-xl border border-white/[0.04]" />
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 pt-2">
          {status === "idle" && !previewUrl && (
            <button
              type="button"
              disabled={disabled}
              onClick={startRecording}
              className={cn(ui.btnPrimary, "w-full sm:w-auto shadow-[0_0_20px_rgba(204,255,0,0.3)]")}
            >
              <Mic className="h-4 w-4" />
              Engage Microphone
            </button>
          )}

          {status === "recording" && (
            <>
              <button type="button" onClick={pauseRecording} className={ui.btnSecondary}>
                <Pause className="h-4 w-4" />
                Hold
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnDanger}>
                <Square className="h-4 w-4 fill-current" />
                Complete Buffer
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
                Complete Buffer
              </button>
            </>
          )}

          {previewUrl && status === "idle" && (
            <button type="button" onClick={discard} className={ui.btnSecondary}>
              <RotateCcw className="h-4 w-4" />
              Retake Audio
            </button>
          )}
        </div>
      </div>

      {previewUrl && status === "idle" && (
        <div className="rounded-[20px] border border-cyan-500/20 bg-[#0c121e]/80 p-4 shadow-xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200">
          <div className="mb-2.5 flex items-center justify-between text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-cyan-400">
              <Volume2 className="h-3.5 w-3.5" />
              Captured Acoustic Waveform
            </span>
            <span className="font-mono text-xs text-slate-400">{formatTime(elapsed)}</span>
          </div>
          <audio controls src={previewUrl} preload="metadata" className="w-full" />
        </div>
      )}

      {error && (
        <div className={ui.alertError}>
          <p className="font-mono">{error}</p>
        </div>
      )}
    </div>
  );
}
