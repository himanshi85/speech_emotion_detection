/** Shared design system tokens for high-end SaaS UI */
export const ui = {
  page: "min-h-screen text-slate-900 saas-mesh-bg selection:bg-indigo-500/20",
  header:
    "sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl supports-[backdrop-filter]:bg-white/75 transition-all duration-200",
  card: "rounded-2xl glass-panel p-6 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)]",
  cardElevated: "rounded-2xl glass-panel-elevated p-6 sm:p-7",
  cardMuted: "rounded-2xl border border-slate-200/80 bg-slate-50/70 p-6 sm:p-8",
  sectionTitle: "text-base font-semibold text-slate-900 tracking-tight",
  sectionDesc: "mt-0.5 text-xs text-slate-500 leading-relaxed",
  label: "text-xs font-semibold uppercase tracking-wider text-slate-500",
  input:
    "w-full rounded-xl border border-slate-200 bg-white/90 px-4 py-3 text-sm text-slate-900 shadow-sm transition-all placeholder:text-slate-400 hover:border-slate-300 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-indigo-500/10 disabled:bg-slate-50 disabled:text-slate-400",
  btnPrimary:
    "relative inline-flex items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-700 px-6 py-3.5 text-sm font-semibold text-white shadow-[0_4px_14px_rgba(79,70,229,0.3)] transition-all duration-200 hover:from-indigo-500 hover:via-indigo-600 hover:to-violet-600 hover:shadow-[0_6px_20px_rgba(79,70,229,0.4)] hover:-translate-y-0.5 active:translate-y-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0 disabled:hover:shadow-none",
  btnSecondary:
    "inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white/90 px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 active:scale-[0.98]",
  btnDanger:
    "inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-rose-500 to-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:from-rose-600 hover:to-red-700 active:scale-[0.98]",
  btnWarning:
    "inline-flex items-center justify-center gap-2 rounded-xl border border-amber-300 bg-amber-50/90 px-4 py-2.5 text-sm font-semibold text-amber-900 shadow-sm transition-all hover:bg-amber-100/90 active:scale-[0.98]",
  btnSuccess:
    "inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-300 bg-emerald-50/90 px-4 py-2.5 text-sm font-semibold text-emerald-900 shadow-sm transition-all hover:bg-emerald-100/90 active:scale-[0.98]",
  alertError: "rounded-xl border border-rose-200 bg-rose-50/90 p-4 text-sm text-rose-800 shadow-sm",
  alertWarn: "rounded-xl border border-amber-200 bg-amber-50/90 p-4 text-xs leading-relaxed text-amber-900 shadow-sm",
  segmentWrap: "flex gap-1.5 rounded-xl border border-slate-200/80 bg-slate-100/70 p-1.5 backdrop-blur-sm",
  segmentActive:
    "bg-white text-indigo-700 font-semibold shadow-[0_2px_8px_rgba(15,23,42,0.08)] ring-1 ring-slate-200/80 transition-all duration-200",
  segmentIdle: "text-slate-600 hover:text-slate-900 hover:bg-white/40 transition-all duration-200",
} as const;
