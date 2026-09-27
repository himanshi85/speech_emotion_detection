"use client";

import { Mic, Pause, Play, RotateCcw, Square, Volume2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { DotMatrixNumber } from "@/components/DotMatrixNumber";
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
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
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

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
      ctx.fillRect(0, 0, width, height);

      const numBars = 48;
      const barSpacing = 4;
      const totalSpacing = (numBars - 1) * barSpacing;
      const barWidth = Math.max(2, (width - totalSpacing) / numBars);

      for (let i = 0; i < numBars; i++) {
        const binIndex = Math.floor((i / numBars) * (buffer.length * 0.5));
        const raw = buffer[binIndex] || 0;
        const norm = raw / 255;
        const barHeight = Math.max(3, norm * (height - 8));
        const x = i * (barWidth + barSpacing);
        const y = (height - barHeight) / 2;

        ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    draw();
  }, []);

  const cleanupStream = useCallback(() => {
    stopVisualizer();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
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

  const startRecording = async () => {
    if (disabled) return;
    setError(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    chunksRef.current = [];

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

      const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.85;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mimeType = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
      ].find((t) => MediaRecorder.isTypeSupported(t)) || "";

      const mr = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
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
        onRecordingReady(blob, `live-capture-${Date.now()}.${ext}`);
        cleanupStream();
      };

      mr.start(250);
      startTimeRef.current = Date.now();
      setStatus("recording");
      drawVisualizer();

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
      stopVisualizer();
      setStatus("paused");
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && status === "paused") {
      mediaRecorderRef.current.resume();
      startTimeRef.current += Date.now() - pausedTimeRef.current;
      setStatus("recording");
      drawVisualizer();
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
    <div className="space-y-3.5">
      {/* Visualizer & Timer Display Card */}
      <div className="relative overflow-hidden rounded-[28px] border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/6 pb-3">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full transition-all",
                status === "recording" && "bg-white shadow-[0_0_8px_#ffffff] animate-ping",
                status === "paused" && "bg-amber-400",
                status === "idle" && "bg-white/30",
              )}
            />
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400">
              {status === "recording" && "Live Speech Recording"}
              {status === "paused" && "Paused Buffer"}
              {status === "idle" && (previewUrl ? "Recording Complete" : "Standby Sensor")}
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-xs text-white">
            <DotMatrixNumber value={formatTime(elapsed)} size="xs" dotColor="#ffffff" />
          </div>
        </div>

        <div className="py-3">
          <canvas ref={canvasRef} width={520} height={60} className="h-14 w-full rounded-xl" />
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 pt-1">
          {status === "idle" && !previewUrl && (
            <button
              type="button"
              disabled={disabled}
              onClick={startRecording}
              className={cn(ui.btnPrimary, "w-full sm:w-auto")}
            >
              <Mic className="h-4 w-4" />
              <span>Record Speech</span>
            </button>
          )}

          {status === "recording" && (
            <>
              <button type="button" onClick={pauseRecording} className={ui.btnSecondary}>
                <Pause className="h-3.5 w-3.5" />
                <span>Pause</span>
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnPrimary}>
                <Square className="h-3.5 w-3.5 fill-black" />
                <span>Finish</span>
              </button>
            </>
          )}

          {status === "paused" && (
            <>
              <button type="button" onClick={resumeRecording} className={ui.btnSecondary}>
                <Play className="h-3.5 w-3.5" />
                <span>Resume</span>
              </button>
              <button type="button" onClick={stopRecording} className={ui.btnPrimary}>
                <Square className="h-3.5 w-3.5 fill-black" />
                <span>Finish</span>
              </button>
            </>
          )}

          {previewUrl && status === "idle" && (
            <button type="button" onClick={discard} className={ui.btnSecondary}>
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Record Again</span>
            </button>
          )}
        </div>
      </div>

      {previewUrl && status === "idle" && (
        <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-3.5 backdrop-blur-xl">
          <div className="mb-2 flex items-center justify-between text-xs text-slate-300">
            <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-slate-400">
              <Volume2 className="h-3 w-3" />
              Recorded Speech Preview
            </span>
            <span className="font-mono text-[11px] text-slate-400">{formatTime(elapsed)}</span>
          </div>
          <audio controls src={previewUrl} preload="metadata" className="w-full h-8" />
        </div>
      )}

      {error && (
        <div className={ui.alertError}>
          <p className="font-mono text-xs">{error}</p>
        </div>
      )}
    </div>
  );
}
