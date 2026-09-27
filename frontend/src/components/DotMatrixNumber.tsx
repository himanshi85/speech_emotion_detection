"use client";

import React from "react";

type Props = {
  value: string | number;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  dotColor?: string;
  glowColor?: string;
  showInactive?: boolean;
  className?: string;
};

const FONT_5X7: Record<string, number[]> = {
  "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
  "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
  "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
  "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
  "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
  "5": [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
  "6": [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
  "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
  "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
  "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
  ".": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100],
  ",": [0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000],
  ":": [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
  "%": [0b11001, 0b11010, 0b00100, 0b01000, 0b01011, 0b10011, 0b00000],
  "$": [0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100],
  "-": [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
  "+": [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
  "/": [0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b00000, 0b00000],
  " ": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
};

const SIZES = {
  xs: { dotRadius: 0.9, step: 2.2, charWidth: 11, charHeight: 16, gap: 2 },
  sm: { dotRadius: 1.2, step: 3.0, charWidth: 15, charHeight: 22, gap: 3 },
  md: { dotRadius: 1.6, step: 4.2, charWidth: 21, charHeight: 30, gap: 4 },
  lg: { dotRadius: 2.2, step: 5.8, charWidth: 29, charHeight: 42, gap: 6 },
  xl: { dotRadius: 2.8, step: 7.2, charWidth: 36, charHeight: 52, gap: 7 },
};

export function DotMatrixNumber({
  value,
  size = "md",
  dotColor = "#ffffff",
  glowColor = "rgba(255, 255, 255, 0.45)",
  showInactive = false,
  className = "",
}: Props) {
  const str = String(value);
  const cfg = SIZES[size];
  const totalWidth = str.length * (cfg.charWidth + cfg.gap) - cfg.gap;
  const totalHeight = cfg.charHeight;

  return (
    <svg
      width={Math.max(totalWidth, 1)}
      height={totalHeight}
      viewBox={`0 0 ${totalWidth} ${totalHeight}`}
      className={`inline-block overflow-visible ${className}`}
      style={{
        filter: glowColor ? `drop-shadow(0 0 4px ${glowColor})` : undefined,
      }}
    >
      {str.split("").map((char, charIdx) => {
        const rows = FONT_5X7[char] ?? FONT_5X7[" "];
        const offsetX = charIdx * (cfg.charWidth + cfg.gap);

        return (
          <g key={charIdx} transform={`translate(${offsetX}, 0)`}>
            {rows.map((rowBits, row) => {
              const y = row * cfg.step + cfg.dotRadius;
              return Array.from({ length: 5 }).map((_, col) => {
                const bit = (rowBits >> (4 - col)) & 1;
                const x = col * cfg.step + cfg.dotRadius;

                if (bit === 1) {
                  return (
                    <circle
                      key={`${row}-${col}`}
                      cx={x}
                      cy={y}
                      r={cfg.dotRadius}
                      fill={dotColor}
                    />
                  );
                }

                if (showInactive) {
                  return (
                    <circle
                      key={`${row}-${col}`}
                      cx={x}
                      cy={y}
                      r={cfg.dotRadius * 0.7}
                      fill="none"
                      stroke="rgba(255, 255, 255, 0.08)"
                      strokeWidth={0.5}
                    />
                  );
                }

                return null;
              });
            })}
          </g>
        );
      })}
    </svg>
  );
}
