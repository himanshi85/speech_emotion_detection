/** Shared design system tokens for RonDesignLab-inspired Minimal Premium UI */
export const ui = {
  page: "min-h-screen text-slate-100 canvas-ron selection:bg-white/20 selection:text-white pb-24",
  header:
    "sticky top-0 z-30 border-b border-white/[0.06] bg-[#06070a]/75 backdrop-blur-2xl transition-all duration-200",
  card: "rounded-[32px] squircle-obsidian p-6 sm:p-7 transition-all duration-300 hover:border-white/[0.14]",
  cardElevated: "rounded-[36px] squircle-obsidian p-6 sm:p-8",
  cardMuted: "rounded-[32px] border border-white/[0.06] bg-[#0c101a]/40 p-6 sm:p-8 backdrop-blur-xl",
  squirclePlum:
    "squircle-magenta p-6 sm:p-7 relative overflow-hidden transition-all duration-300 hover:shadow-[0_28px_70px_-10px_rgba(190,24,93,0.45)]",
  squircleEmber:
    "squircle-ember p-6 sm:p-7 relative overflow-hidden transition-all duration-300 hover:shadow-[0_28px_70px_-10px_rgba(234,88,12,0.45)]",
  squircleIndigo:
    "squircle-indigo p-6 sm:p-7 relative overflow-hidden transition-all duration-300 hover:shadow-[0_28px_70px_-10px_rgba(67,56,202,0.45)]",
  squircleObsidian:
    "squircle-obsidian p-6 sm:p-7 relative overflow-hidden transition-all duration-300",
  sectionTitle: "text-xs font-semibold uppercase tracking-wider text-slate-300",
  sectionDesc: "mt-0.5 text-xs text-slate-400 leading-relaxed",
  label: "text-[10px] font-semibold uppercase tracking-widest text-slate-400",
  input:
    "w-full rounded-2xl border border-white/[0.1] bg-[#0d121d]/80 px-4 py-3 text-sm text-white shadow-inner transition-all placeholder:text-slate-500 hover:border-white/[0.18] focus:border-white focus:bg-[#101726] focus:outline-none disabled:bg-slate-900/40 disabled:text-slate-600",
  btnPrimary:
    "relative inline-flex items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-xs font-bold tracking-wider text-black shadow-[0_4px_20px_rgba(255,255,255,0.25)] transition-all duration-200 hover:scale-[1.02] hover:shadow-[0_6px_25px_rgba(255,255,255,0.35)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:scale-100",
  btnSecondary:
    "inline-flex items-center justify-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.05] px-4 py-2 text-xs font-medium tracking-wider text-slate-200 transition-all hover:border-white/[0.22] hover:bg-white/[0.08] hover:text-white active:scale-[0.98]",
  btnDanger:
    "inline-flex items-center justify-center gap-2 rounded-full border border-rose-500/30 bg-rose-950/40 px-3.5 py-1.5 text-xs font-medium text-rose-300 transition-all hover:bg-rose-900/50 active:scale-[0.98]",
  btnCircleWhite: "btn-circle-white",
  btnCircleDark: "btn-circle-dark",
  pillWhiteActive:
    "bg-white text-black font-semibold rounded-full px-5 py-2 text-xs shadow-md transition-all",
  pillIdle:
    "text-slate-400 hover:text-white font-medium rounded-full px-4 py-2 text-xs transition-all",
  alertError: "rounded-2xl border border-rose-500/30 bg-rose-950/40 p-4 text-xs font-medium text-rose-200 shadow-lg backdrop-blur-md",
  alertWarn: "rounded-2xl border border-amber-500/30 bg-amber-950/40 p-4 text-xs font-medium text-amber-200 shadow-lg backdrop-blur-md",
  segmentWrap: "flex gap-1 rounded-full border border-white/[0.08] bg-[#0a0e17]/80 p-1 backdrop-blur-xl",
  segmentActive:
    "bg-white text-black font-semibold shadow-sm transition-all duration-200 rounded-full",
  segmentIdle: "text-slate-400 hover:text-white transition-all duration-200 rounded-full",
} as const;
