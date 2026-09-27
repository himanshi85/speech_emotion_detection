/** Shared design system tokens for RonDesignLab-inspired Cyber-Glass UI */
export const ui = {
  page: "min-h-screen text-slate-100 cyber-canvas-bg selection:bg-lime-400/20 selection:text-lime-300 pb-28",
  header:
    "sticky top-0 z-30 border-b border-white/[0.08] bg-[#06080d]/80 backdrop-blur-2xl transition-all duration-200",
  card: "rounded-[28px] cyber-glass p-6 sm:p-7 transition-all duration-300 hover:border-white/[0.14] hover:shadow-[0_20px_45px_rgba(0,0,0,0.85)]",
  cardElevated: "rounded-[32px] cyber-glass-elevated p-6 sm:p-8",
  cardMuted: "rounded-[28px] border border-white/[0.06] bg-[#0c101a]/50 p-6 sm:p-8 backdrop-blur-xl",
  sectionTitle: "text-sm font-bold uppercase tracking-wider text-slate-200",
  sectionDesc: "mt-0.5 text-xs text-slate-400 leading-relaxed",
  label: "text-[11px] font-bold uppercase tracking-widest text-slate-400",
  input:
    "w-full rounded-2xl border border-white/[0.1] bg-[#0d121d]/80 px-4 py-3 text-sm text-white shadow-inner transition-all placeholder:text-slate-500 hover:border-white/[0.18] focus:border-cyan-400 focus:bg-[#101726] focus:outline-none focus:ring-2 focus:ring-cyan-400/20 disabled:bg-slate-900/40 disabled:text-slate-600",
  btnPrimary:
    "relative inline-flex items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-lime-400 via-lime-300 to-emerald-400 px-6 py-3.5 text-xs font-extrabold uppercase tracking-wider text-slate-950 shadow-[0_0_24px_rgba(204,255,0,0.35)] transition-all duration-200 hover:shadow-[0_0_36px_rgba(204,255,0,0.55)] hover:scale-[1.02] active:scale-[0.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-lime-400 disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:scale-100 disabled:hover:shadow-none",
  btnSecondary:
    "inline-flex items-center justify-center gap-2 rounded-2xl border border-white/[0.12] bg-white/[0.04] px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-200 shadow-sm backdrop-blur-md transition-all hover:border-white/[0.22] hover:bg-white/[0.08] hover:text-white active:scale-[0.98]",
  btnDanger:
    "inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-500/40 bg-rose-950/40 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-rose-300 shadow-[0_0_16px_rgba(244,63,94,0.2)] transition-all hover:bg-rose-900/50 hover:border-rose-400 active:scale-[0.98]",
  btnSuccess:
    "inline-flex items-center justify-center gap-2 rounded-2xl border border-emerald-500/40 bg-emerald-950/40 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-emerald-300 shadow-[0_0_16px_rgba(16,185,129,0.2)] transition-all hover:bg-emerald-900/50 active:scale-[0.98]",
  alertError: "rounded-2xl border border-rose-500/30 bg-rose-950/40 p-4 text-xs font-medium text-rose-200 shadow-lg backdrop-blur-md",
  alertWarn: "rounded-2xl border border-amber-500/30 bg-amber-950/40 p-4 text-xs font-medium text-amber-200 shadow-lg backdrop-blur-md",
  segmentWrap: "flex gap-1.5 rounded-2xl border border-white/[0.08] bg-[#0a0e17]/80 p-1.5 backdrop-blur-xl",
  segmentActive:
    "bg-white/[0.12] text-white font-bold shadow-[0_2px_12px_rgba(0,0,0,0.5)] border border-white/[0.18] transition-all duration-200",
  segmentIdle: "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] transition-all duration-200",
} as const;
