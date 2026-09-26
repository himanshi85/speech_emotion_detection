export type EmotionDetail = {
  label: string;
  emoji: string;
  description: string;
  color: string;
  barColor: string;
  gradient: string;
  badge: string;
  lightBg: string;
  borderColor: string;
  textColor: string;
  tag: string;
};

export const EMOTION_META: Record<string, EmotionDetail> = {
  neutral: {
    label: "Neutral",
    emoji: "😐",
    description: "Even-toned, balanced pitch baseline with steady cadence.",
    color: "#64748b",
    barColor: "from-slate-500 to-slate-600",
    gradient: "from-slate-500/10 via-slate-500/5 to-transparent",
    badge: "bg-slate-100 text-slate-800 ring-slate-300",
    lightBg: "bg-slate-50",
    borderColor: "border-slate-200",
    textColor: "text-slate-700",
    tag: "Equilibrium",
  },
  calm: {
    label: "Calm",
    emoji: "😌",
    description: "Relaxed prosody with lower acoustic intensity and serene rhythm.",
    color: "#0d9488",
    barColor: "from-teal-500 to-emerald-500",
    gradient: "from-teal-500/15 via-emerald-500/5 to-transparent",
    badge: "bg-teal-50 text-teal-800 ring-teal-200",
    lightBg: "bg-teal-50/60",
    borderColor: "border-teal-200",
    textColor: "text-teal-800",
    tag: "Tranquil",
  },
  happy: {
    label: "Happy",
    emoji: "✨",
    description: "Elevated fundamental frequency with dynamic pitch contours.",
    color: "#f59e0b",
    barColor: "from-amber-400 via-amber-500 to-orange-500",
    gradient: "from-amber-500/15 via-amber-400/5 to-transparent",
    badge: "bg-amber-50 text-amber-900 ring-amber-300",
    lightBg: "bg-amber-50/70",
    borderColor: "border-amber-200",
    textColor: "text-amber-800",
    tag: "High Valence",
  },
  sad: {
    label: "Sad",
    emoji: "💧",
    description: "Attenuated amplitude with downward pitch glides and slower tempo.",
    color: "#3b82f6",
    barColor: "from-sky-400 via-blue-500 to-indigo-500",
    gradient: "from-blue-500/15 via-sky-400/5 to-transparent",
    badge: "bg-blue-50 text-blue-800 ring-blue-200",
    lightBg: "bg-blue-50/60",
    borderColor: "border-blue-200",
    textColor: "text-blue-800",
    tag: "Melancholy",
  },
  angry: {
    label: "Angry",
    emoji: "🔥",
    description: "High vocal strain, sharp acoustic bursts, and rapid energy peaks.",
    color: "#ef4444",
    barColor: "from-rose-500 via-red-500 to-red-600",
    gradient: "from-red-500/15 via-rose-500/5 to-transparent",
    badge: "bg-red-50 text-red-800 ring-red-200",
    lightBg: "bg-red-50/60",
    borderColor: "border-red-200",
    textColor: "text-red-800",
    tag: "High Arousal",
  },
  fearful: {
    label: "Fearful",
    emoji: "⚡",
    description: "Subtle vocal jitter, unstable harmonics, and tense frequency shifts.",
    color: "#8b5cf6",
    barColor: "from-violet-500 via-purple-500 to-indigo-600",
    gradient: "from-violet-500/15 via-purple-500/5 to-transparent",
    badge: "bg-violet-50 text-violet-800 ring-violet-200",
    lightBg: "bg-violet-50/60",
    borderColor: "border-violet-200",
    textColor: "text-violet-800",
    tag: "Tension",
  },
  disgust: {
    label: "Disgust",
    emoji: "🍃",
    description: "Throaty vocal resonance, drawn vowels, and lower harmonic variation.",
    color: "#16a34a",
    barColor: "from-lime-500 via-emerald-500 to-green-600",
    gradient: "from-emerald-500/15 via-lime-500/5 to-transparent",
    badge: "bg-emerald-50 text-emerald-800 ring-emerald-200",
    lightBg: "bg-emerald-50/60",
    borderColor: "border-emerald-200",
    textColor: "text-emerald-800",
    tag: "Aversive",
  },
  surprised: {
    label: "Surprised",
    emoji: "🌟",
    description: "Sudden high-pitch jump, wide vocal range, and quick onset.",
    color: "#ec4899",
    barColor: "from-pink-500 via-fuchsia-500 to-purple-500",
    gradient: "from-fuchsia-500/15 via-pink-500/5 to-transparent",
    badge: "bg-fuchsia-50 text-fuchsia-800 ring-fuchsia-200",
    lightBg: "bg-fuchsia-50/60",
    borderColor: "border-fuchsia-200",
    textColor: "text-fuchsia-800",
    tag: "Startle Reaction",
  },
};

export function emotionMeta(key: string): EmotionDetail {
  const normalized = key.trim().toLowerCase();
  return (
    EMOTION_META[normalized] ?? {
      label: key,
      emoji: "🎙️",
      description: "Speech acoustics classified across neural emotion distribution.",
      color: "#6366f1",
      barColor: "from-indigo-500 to-violet-500",
      gradient: "from-indigo-500/15 to-transparent",
      badge: "bg-indigo-50 text-indigo-800 ring-indigo-200",
      lightBg: "bg-indigo-50/60",
      borderColor: "border-indigo-200",
      textColor: "text-indigo-800",
      tag: "Classified",
    }
  );
}
