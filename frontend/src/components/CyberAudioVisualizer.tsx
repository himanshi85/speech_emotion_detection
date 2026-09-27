"use client";

import { useEffect, useRef } from "react";

type Props = {
  isActive?: boolean;
  intensity?: number;
  primaryColor?: string;
  glowColor?: string;
  emotionLabel?: string;
  className?: string;
};

export function CyberAudioVisualizer({
  isActive = false,
  intensity = 0.5,
  primaryColor = "#00f0ff",
  glowColor = "rgba(0, 240, 255, 0.4)",
  emotionLabel,
  className = "w-full h-44",
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const stateRef = useRef({
    angleX: 0.2,
    angleY: 0,
    targetAngleY: 0,
    speed: 0.012,
    pulse: 0,
    particles: Array.from({ length: 48 }, () => ({
      theta: Math.random() * Math.PI * 2,
      phi: Math.acos(Math.random() * 2 - 1),
      radius: 55 + Math.random() * 25,
      size: 1 + Math.random() * 1.5,
      speed: 0.006 + Math.random() * 0.012,
    })),
  });

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

    const render = () => {
      const s = stateRef.current;
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const baseRadius = Math.min(width, height) * 0.26;
      const activeMult = isActive ? 1.0 + intensity * 0.35 : 1.0;
      const currentRadius = baseRadius * activeMult;

      s.angleY += isActive ? 0.024 : 0.008;
      s.pulse += isActive ? 0.08 : 0.03;

      // 1. Core Ambient Halo
      const haloGrad = ctx.createRadialGradient(
        centerX,
        centerY,
        currentRadius * 0.2,
        centerX,
        centerY,
        currentRadius * 1.8,
      );
      haloGrad.addColorStop(0, glowColor);
      haloGrad.addColorStop(0.5, "rgba(13, 17, 26, 0.2)");
      haloGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = haloGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius * 1.8, 0, Math.PI * 2);
      ctx.fill();

      // 2. Projected 3D Orbital Rings (Gyroscope Architecture)
      const drawRing = (tiltX: number, rotY: number, radX: number, radY: number, alpha: number) => {
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(rotY);
        ctx.scale(1, Math.cos(tiltX));

        ctx.beginPath();
        ctx.arc(0, 0, radX, 0, Math.PI * 2);
        ctx.strokeStyle = primaryColor;
        ctx.globalAlpha = alpha;
        ctx.lineWidth = 1.8;
        ctx.shadowColor = primaryColor;
        ctx.shadowBlur = isActive ? 16 : 8;
        ctx.stroke();

        // Node markers along ring
        const numNodes = 4;
        for (let i = 0; i < numNodes; i++) {
          const a = (i * Math.PI * 2) / numNodes + s.pulse * 0.5;
          const nx = Math.cos(a) * radX;
          const ny = Math.sin(a) * radY;
          ctx.beginPath();
          ctx.arc(nx, ny, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = "#ffffff";
          ctx.shadowBlur = 12;
          ctx.fill();
        }

        ctx.restore();
      };

      // Outer Translucent Ring
      drawRing(
        0.85,
        s.angleY,
        currentRadius * 1.25,
        currentRadius * 1.25,
        isActive ? 0.85 : 0.45,
      );

      // Intermediate Cross Ring
      drawRing(
        1.1,
        -s.angleY * 0.8 + Math.PI / 4,
        currentRadius * 1.05,
        currentRadius * 1.05,
        isActive ? 0.75 : 0.35,
      );

      // Inner Equator Ring
      drawRing(
        0.5,
        s.angleY * 1.3,
        currentRadius * 0.85,
        currentRadius * 0.85,
        isActive ? 0.95 : 0.55,
      );

      // 3. Dynamic Waveform Ribbon / Spherical Contour
      ctx.beginPath();
      const wavePoints = 36;
      for (let i = 0; i <= wavePoints; i++) {
        const theta = (i * Math.PI * 2) / wavePoints;
        const waveOffset = Math.sin(theta * 6 + s.pulse * 2) * (isActive ? 12 * intensity : 3);
        const r = currentRadius * 0.68 + waveOffset;
        const px = centerX + Math.cos(theta + s.angleY) * r;
        const py = centerY + Math.sin(theta) * r * 0.6;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.strokeStyle = "#ffffff";
      ctx.globalAlpha = isActive ? 0.75 : 0.3;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 4. Floating 3D Depth Particles
      ctx.shadowBlur = 6;
      for (const p of s.particles) {
        p.theta += p.speed;
        const x3d = p.radius * Math.sin(p.phi) * Math.cos(p.theta);
        const y3d = p.radius * Math.sin(p.phi) * Math.sin(p.theta);
        const z3d = p.radius * Math.cos(p.phi);

        // Simple perspective projection
        const scale = 220 / (220 + z3d);
        const px = centerX + x3d * scale * (width / 400);
        const py = centerY + y3d * scale * (height / 200) * 0.65;
        const alpha = Math.max(0.15, Math.min(0.9, (z3d + p.radius) / (p.radius * 2)));

        ctx.fillStyle = primaryColor;
        ctx.globalAlpha = alpha * (isActive ? 1 : 0.5);
        ctx.beginPath();
        ctx.arc(px, py, p.size * scale * (isActive ? 1.4 : 1), 0, Math.PI * 2);
        ctx.fill();
      }

      // 5. Central Holographic Core
      const coreGrad = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        currentRadius * 0.45,
      );
      coreGrad.addColorStop(0, "#ffffff");
      coreGrad.addColorStop(0.3, primaryColor);
      coreGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = coreGrad;
      ctx.globalAlpha = isActive ? 0.9 : 0.6;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius * 0.45, 0, Math.PI * 2);
      ctx.fill();

      // 6. Center Technical Core Crosshairs
      ctx.globalAlpha = 0.4;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(centerX - 10, centerY);
      ctx.lineTo(centerX + 10, centerY);
      ctx.moveTo(centerX, centerY - 10);
      ctx.lineTo(centerX, centerY + 10);
      ctx.stroke();

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isActive, intensity, primaryColor, glowColor]);

  return (
    <div className={`relative flex items-center justify-center overflow-hidden rounded-[24px] bg-[#070a12]/60 border border-white/[0.06] backdrop-blur-xl ${className}`}>
      <canvas ref={canvasRef} className="h-full w-full pointer-events-none" />

      {/* Cockpit HUD Overlays */}
      <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-1.5 rounded-full border border-white/[0.1] bg-[#0d121f]/80 px-2.5 py-1 text-[9px] font-bold tracking-widest text-slate-300 backdrop-blur-md">
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{
            backgroundColor: primaryColor,
            boxShadow: `0 0 8px ${primaryColor}`,
          }}
        />
        <span>{isActive ? "RESONANCE ACTIVE" : "SPATIAL STANDBY"}</span>
      </div>

      {emotionLabel && (
        <div className="pointer-events-none absolute right-3 top-3 rounded-full border border-white/[0.1] bg-[#0d121f]/80 px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider text-slate-300 backdrop-blur-md">
          {emotionLabel}
        </div>
      )}

      <div className="pointer-events-none absolute bottom-2.5 left-3 text-[9px] font-mono uppercase tracking-widest text-slate-500">
        3D GYROSCOPE // 16 kHz
      </div>
      <div className="pointer-events-none absolute bottom-2.5 right-3 text-[9px] font-mono uppercase tracking-widest text-slate-500">
        PROSODY HARMONIC
      </div>
    </div>
  );
}
