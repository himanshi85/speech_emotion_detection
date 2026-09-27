export type EmotionDetail = {
  label: string;
  color: string;
  barColor: string;
  badge: string;
  textColor: string;
  description: string;
};

export const EMOTION_META: Record<string, EmotionDetail> = {
  neutral: {
    label: "Neutral",
    color: "#64748b",
    barColor: "bg-slate-500",
    badge: "border-slate-200 bg-slate-50 text-slate-700",
    textColor: "text-slate-800",
    description: "Balanced, steady pitch with even cadence and neutral tone.",
  },
  calm: {
    label: "Calm",
    color: "#059669",
    barColor: "bg-emerald-500",
    badge: "border-emerald-200 bg-emerald-50 text-emerald-800",
    textColor: "text-emerald-900",
    description: "Relaxed vocal intensity, slower tempo, and gentle intonation.",
  },
  happy: {
    label: "Happy",
    color: "#d97706",
    barColor: "bg-amber-500",
    badge: "border-amber-200 bg-amber-50 text-amber-800",
    textColor: "text-amber-900",
    description: "Elevated pitch, lively rhythm, and expressive variations.",
  },
  sad: {
    label: "Sad",
    color: "#4f46e5",
    barColor: "bg-indigo-500",
    badge: "border-indigo-200 bg-indigo-50 text-indigo-800",
    textColor: "text-indigo-900",
    description: "Lower pitch contour, decreased vocal energy, and frequent pauses.",
  },
  angry: {
    label: "Angry",
    color: "#dc2626",
    barColor: "bg-rose-500",
    badge: "border-rose-200 bg-rose-50 text-rose-800",
    textColor: "text-rose-900",
    description: "High vocal intensity, sharp pitch onsets, and abrupt energy bursts.",
  },
  fearful: {
    label: "Fearful",
    color: "#7c3aed",
    barColor: "bg-purple-500",
    badge: "border-purple-200 bg-purple-50 text-purple-800",
    textColor: "text-purple-900",
    description: "Fast tempo, irregular pitch fluctuations, and breathless delivery.",
  },
  disgust: {
    label: "Disgust",
    color: "#0d9488",
    barColor: "bg-teal-600",
    badge: "border-teal-200 bg-teal-50 text-teal-800",
    textColor: "text-teal-900",
    description: "Lower register with drawn-out vowels and downward pitch glides.",
  },
  surprised: {
    label: "Surprised",
    color: "#ea580c",
    barColor: "bg-orange-500",
    badge: "border-orange-200 bg-orange-50 text-orange-800",
    textColor: "text-orange-900",
    description: "Abrupt rise in fundamental frequency with expanded vocal range.",
  },
};

export function emotionMeta(key: string): EmotionDetail {
  const normalized = key.trim().toLowerCase();
  return (
    EMOTION_META[normalized] ?? {
      label: key.charAt(0).toUpperCase() + key.slice(1),
      color: "#2563eb",
      barColor: "bg-blue-500",
      badge: "border-blue-200 bg-blue-50 text-blue-800",
      textColor: "text-blue-900",
      description: "Acoustic pattern classified across neural probability distribution.",
    }
  );
}
