export type EmotionDetail = {
  label: string;
  code: string;
  description: string;
  color: string;
  glowColor: string;
  barColor: string;
  gradient: string;
  badge: string;
  borderGlow: string;
  textColor: string;
  tag: string;
  valence: string;
  arousal: string;
};

export const EMOTION_META: Record<string, EmotionDetail> = {
  neutral: {
    label: "Neutral",
    code: "NEU-01",
    description: "Equilibrium baseline. Linear fundamental frequency and rhythmic cadence.",
    color: "#38bdf8",
    glowColor: "rgba(56, 189, 248, 0.4)",
    barColor: "from-sky-500 via-cyan-400 to-teal-400",
    gradient: "from-sky-500/20 via-cyan-500/10 to-transparent",
    badge: "border-sky-500/30 bg-sky-950/40 text-sky-300 shadow-[0_0_12px_rgba(56,189,248,0.2)]",
    borderGlow: "border-sky-500/40 shadow-[0_0_20px_rgba(56,189,248,0.15)]",
    textColor: "text-sky-300",
    tag: "Equilibrium",
    valence: "0.00",
    arousal: "Low",
  },
  calm: {
    label: "Calm",
    code: "CLM-02",
    description: "Tranquil prosodic profile with relaxed vocal intensity and unhurried tempo.",
    color: "#00f59b",
    glowColor: "rgba(0, 245, 155, 0.4)",
    barColor: "from-emerald-500 via-teal-400 to-cyan-400",
    gradient: "from-emerald-500/20 via-teal-500/10 to-transparent",
    badge: "border-emerald-500/30 bg-emerald-950/40 text-emerald-300 shadow-[0_0_12px_rgba(0,245,155,0.2)]",
    borderGlow: "border-emerald-500/40 shadow-[0_0_20px_rgba(0,245,155,0.15)]",
    textColor: "text-emerald-300",
    tag: "Tranquil",
    valence: "+0.45",
    arousal: "Low",
  },
  happy: {
    label: "Happy",
    code: "HPY-03",
    description: "Elevated fundamental frequency with wide dynamic pitch contours and high energy.",
    color: "#ccff00",
    glowColor: "rgba(204, 255, 0, 0.45)",
    barColor: "from-lime-400 via-yellow-400 to-amber-400",
    gradient: "from-lime-500/25 via-yellow-500/10 to-transparent",
    badge: "border-lime-400/40 bg-lime-950/40 text-lime-300 shadow-[0_0_16px_rgba(204,255,0,0.25)]",
    borderGlow: "border-lime-400/50 shadow-[0_0_25px_rgba(204,255,0,0.2)]",
    textColor: "text-lime-300",
    tag: "High Valence",
    valence: "+0.88",
    arousal: "High",
  },
  sad: {
    label: "Sad",
    code: "SAD-04",
    description: "Attenuated amplitude with downward pitch glides and lengthened pause durations.",
    color: "#818cf8",
    glowColor: "rgba(129, 140, 248, 0.4)",
    barColor: "from-indigo-500 via-blue-500 to-violet-500",
    gradient: "from-indigo-500/20 via-blue-500/10 to-transparent",
    badge: "border-indigo-500/30 bg-indigo-950/40 text-indigo-300 shadow-[0_0_12px_rgba(129,140,248,0.2)]",
    borderGlow: "border-indigo-500/40 shadow-[0_0_20px_rgba(129,140,248,0.15)]",
    textColor: "text-indigo-300",
    tag: "Melancholy",
    valence: "-0.72",
    arousal: "Low",
  },
  angry: {
    label: "Angry",
    code: "ANG-05",
    description: "Acoustic strain, rapid burst transitions, and intense spectral energy spikes.",
    color: "#ff3366",
    glowColor: "rgba(255, 51, 102, 0.45)",
    barColor: "from-rose-500 via-red-500 to-orange-500",
    gradient: "from-rose-500/25 via-red-500/10 to-transparent",
    badge: "border-rose-500/40 bg-rose-950/40 text-rose-300 shadow-[0_0_16px_rgba(255,51,102,0.25)]",
    borderGlow: "border-rose-500/50 shadow-[0_0_25px_rgba(255,51,102,0.2)]",
    textColor: "text-rose-300",
    tag: "High Arousal",
    valence: "-0.65",
    arousal: "Maximum",
  },
  fearful: {
    label: "Fearful",
    code: "FEA-06",
    description: "Micro-tremor frequency perturbation, high spectral jitter, and tense harmonics.",
    color: "#c084fc",
    glowColor: "rgba(192, 132, 252, 0.4)",
    barColor: "from-purple-500 via-violet-500 to-fuchsia-500",
    gradient: "from-purple-500/20 via-violet-500/10 to-transparent",
    badge: "border-purple-500/30 bg-purple-950/40 text-purple-300 shadow-[0_0_12px_rgba(192,132,252,0.2)]",
    borderGlow: "border-purple-500/40 shadow-[0_0_20px_rgba(192,132,252,0.15)]",
    textColor: "text-purple-300",
    tag: "Tension",
    valence: "-0.54",
    arousal: "High",
  },
  disgust: {
    label: "Disgust",
    code: "DIS-07",
    description: "Pharyngeal constriction with drawn vowels and flattened intonation contours.",
    color: "#a3e635",
    glowColor: "rgba(163, 230, 53, 0.4)",
    barColor: "from-lime-500 via-emerald-500 to-green-600",
    gradient: "from-lime-500/20 via-emerald-500/10 to-transparent",
    badge: "border-lime-500/30 bg-lime-950/40 text-lime-300 shadow-[0_0_12px_rgba(163,230,53,0.2)]",
    borderGlow: "border-lime-500/40 shadow-[0_0_20px_rgba(163,230,53,0.15)]",
    textColor: "text-lime-300",
    tag: "Aversive",
    valence: "-0.60",
    arousal: "Moderate",
  },
  surprised: {
    label: "Surprised",
    code: "SRP-08",
    description: "Sudden fundamental frequency leap with expanded vocal range and abrupt onset.",
    color: "#f43f5e",
    glowColor: "rgba(244, 63, 94, 0.4)",
    barColor: "from-pink-500 via-rose-400 to-amber-400",
    gradient: "from-pink-500/20 via-rose-500/10 to-transparent",
    badge: "border-pink-500/30 bg-pink-950/40 text-pink-300 shadow-[0_0_12px_rgba(244,63,94,0.2)]",
    borderGlow: "border-pink-500/40 shadow-[0_0_20px_rgba(244,63,94,0.15)]",
    textColor: "text-pink-300",
    tag: "Startle",
    valence: "+0.20",
    arousal: "Maximum",
  },
};

export function emotionMeta(key: string): EmotionDetail {
  const normalized = key.trim().toLowerCase();
  return (
    EMOTION_META[normalized] ?? {
      label: key.toUpperCase(),
      code: "SER-00",
      description: "Acoustic speech classified across neural foundation logit distribution.",
      color: "#00f0ff",
      glowColor: "rgba(0, 240, 255, 0.4)",
      barColor: "from-cyan-500 to-blue-500",
      gradient: "from-cyan-500/20 to-transparent",
      badge: "border-cyan-500/30 bg-cyan-950/40 text-cyan-300 shadow-[0_0_12px_rgba(0,240,255,0.2)]",
      borderGlow: "border-cyan-500/40 shadow-[0_0_20px_rgba(0,240,255,0.15)]",
      textColor: "text-cyan-300",
      tag: "Classified",
      valence: "0.00",
      arousal: "Dynamic",
    }
  );
}
