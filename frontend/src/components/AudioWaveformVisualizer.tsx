"use client";

import React, { useEffect, useRef } from "react";

type Props = {
  stream?: MediaStream | null;
  audioRef?: React.RefObject<HTMLAudioElement | null>;
  isPlaying?: boolean;
  isRecording?: boolean;
  className?: string;
};

export function AudioWaveformVisualizer({
  stream,
  audioRef,
  isPlaying = false,
  isRecording = false,
  className = "w-full h-24",
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | MediaElementAudioSourceNode | null>(null);

  // Setup Web Audio Analyser when stream or audio element is active
  useEffect(() => {
    let ctx = audioCtxRef.current;
    if (!ctx && (isRecording || isPlaying)) {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtxClass) {
        ctx = new AudioCtxClass();
        audioCtxRef.current = ctx;
      }
    }

    if (!ctx) return;

    if (ctx.state === "suspended" && (isRecording || isPlaying)) {
      ctx.resume().catch(() => {});
    }

    try {
      if (isRecording && stream) {
        if (sourceRef.current) {
          sourceRef.current.disconnect();
          sourceRef.current = null;
        }
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 128;
        analyser.smoothingTimeConstant = 0.8;
        const src = ctx.createMediaStreamSource(stream);
        src.connect(analyser);
        analyserRef.current = analyser;
        sourceRef.current = src;
      } else if (isPlaying && audioRef?.current) {
        if (!sourceRef.current) {
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 128;
          analyser.smoothingTimeConstant = 0.8;
          const src = ctx.createMediaElementSource(audioRef.current);
          src.connect(analyser);
          analyser.connect(ctx.destination);
          analyserRef.current = analyser;
          sourceRef.current = src;
        }
      }
    } catch {
      // Audio node already connected or not allowed
    }

    return () => {
      // Cleanup happens when unmounted or stream stops
    };
  }, [stream, isRecording, isPlaying, audioRef]);

  // Animation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.offsetWidth * 2);
    let height = (canvas.height = canvas.offsetHeight * 2);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth * 2;
      height = canvas.height = canvas.offsetHeight * 2;
    };
    window.addEventListener("resize", handleResize);

    const numBars = 44;
    const dataArray = new Uint8Array(64);
    let idlePhase = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const isActive = isRecording || isPlaying;
      if (isActive && analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray);
      }

      idlePhase += 0.04;
      const barSpacing = 4;
      const totalSpacing = (numBars - 1) * barSpacing;
      const barWidth = Math.max(3, (width - totalSpacing) / numBars);

      for (let i = 0; i < numBars; i++) {
        let val = 0;
        if (isActive && analyserRef.current) {
          // Map frequency bins evenly
          const binIdx = Math.floor((i / numBars) * (dataArray.length * 0.7));
          val = (dataArray[binIdx] || 0) / 255;
        } else {
          // Gentle resting sinusoidal wave
          val = 0.08 + 0.04 * Math.sin(idlePhase + i * 0.25);
        }

        const barHeight = Math.max(4, val * (height * 0.85));
        const x = i * (barWidth + barSpacing);
        const y = (height - barHeight) / 2;

        // Smooth subtle charcoal/slate vertical bars
        if (isActive) {
          ctx.fillStyle = i % 2 === 0 ? "#0f172a" : "#334155";
        } else {
          ctx.fillStyle = "#cbd5e1";
        }

        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
        ctx.fill();
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isPlaying, isRecording]);

  return (
    <div className={`relative flex items-center justify-center rounded-2xl bg-slate-50 border border-slate-200/80 p-3 overflow-hidden ${className}`}>
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  );
}
