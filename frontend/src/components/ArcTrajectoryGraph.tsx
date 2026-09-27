"use client";

import React from "react";

type Props = {
  mode?: "arcs" | "dot-grid";
  accentColor?: string;
  className?: string;
};

export function ArcTrajectoryGraph({
  mode = "arcs",
  accentColor = "#ffffff",
  className = "w-full h-24",
}: Props) {
  if (mode === "dot-grid") {
    // 4 rows x 8 columns of hollow & filled dots like the Total Balance card in the reference
    const rows = 4;
    const cols = 8;
    const pattern = [
      [0, 1, 0, 0, 1, 0, 0, 1],
      [1, 0, 1, 0, 0, 1, 0, 0],
      [0, 0, 0, 1, 0, 0, 1, 1],
      [1, 0, 0, 0, 1, 0, 0, 1],
    ];

    return (
      <div className={`flex flex-col items-center justify-center gap-2.5 ${className}`}>
        {pattern.map((row, rIdx) => (
          <div key={rIdx} className="flex items-center gap-4">
            {row.map((val, cIdx) => (
              <span
                key={cIdx}
                className="inline-block transition-all duration-300"
                style={{
                  width: val ? "5px" : "4px",
                  height: val ? "5px" : "4px",
                  borderRadius: "50%",
                  backgroundColor: val ? accentColor : "transparent",
                  border: val ? "none" : "1px solid rgba(255, 255, 255, 0.22)",
                  boxShadow: val ? `0 0 8px ${accentColor}` : "none",
                }}
              />
            ))}
          </div>
        ))}
      </div>
    );
  }

  // mode === "arcs" (Concentric dashed intersecting arcs with glowing beads like the Lung Capacity & Breath Volume cards)
  return (
    <div className={`relative flex items-center justify-center overflow-hidden ${className}`}>
      <svg
        viewBox="0 0 240 100"
        className="w-full h-full overflow-visible"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="arcGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={accentColor} stopOpacity="0.8" />
            <stop offset="100%" stopColor={accentColor} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Outer subtle baseline */}
        <line
          x1="20"
          y1="82"
          x2="220"
          y2="82"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="0.8"
          strokeDasharray="2 3"
        />

        {/* Arc 1: Left intersecting dashed circle arc */}
        <path
          d="M 40 82 A 50 45 0 0 1 140 82"
          stroke="rgba(255, 255, 255, 0.22)"
          strokeWidth="1"
          strokeDasharray="3 4"
        />

        {/* Arc 2: Center higher intersecting dashed circle arc */}
        <path
          d="M 70 82 A 65 58 0 0 1 200 82"
          stroke="rgba(255, 255, 255, 0.3)"
          strokeWidth="1"
          strokeDasharray="2 3"
        />

        {/* Arc 3: Right smaller arc */}
        <path
          d="M 120 82 A 45 40 0 0 1 210 82"
          stroke="rgba(255, 255, 255, 0.18)"
          strokeWidth="1"
          strokeDasharray="3 4"
        />

        {/* Glowing orbital beads / nodes along trajectory */}
        <circle cx="68" cy="56" r="2.5" fill="#ffffff" filter="drop-shadow(0 0 4px rgba(255,255,255,0.9))" />
        <circle cx="112" cy="74" r="2" fill="#ffffff" filter="drop-shadow(0 0 3px rgba(255,255,255,0.7))" />
        <circle cx="140" cy="24" r="3" fill="#ffffff" filter="drop-shadow(0 0 6px #ffffff)" />
        <circle cx="178" cy="62" r="2.2" fill={accentColor} filter={`drop-shadow(0 0 5px ${accentColor})`} />
      </svg>
    </div>
  );
}
