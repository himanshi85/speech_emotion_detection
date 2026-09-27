/** Clean minimal white mode design tokens */
export const ui = {
  page: "min-h-screen bg-slate-50 text-slate-900 pb-16",
  header: "sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-md",
  card: "rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs",
  cardElevated: "rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs",
  cardMuted: "rounded-2xl border border-slate-200/60 bg-slate-50/70 p-6",
  sectionTitle: "text-sm font-semibold text-slate-900",
  sectionDesc: "text-xs text-slate-500 mt-0.5 leading-relaxed",
  label: "text-xs font-medium text-slate-700",
  input:
    "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-xs transition-all focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 disabled:bg-slate-50 disabled:text-slate-400",
  btnPrimary:
    "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition-all hover:bg-slate-800 active:scale-98 disabled:opacity-40 disabled:cursor-not-allowed",
  btnSecondary:
    "inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 shadow-xs transition-all hover:bg-slate-50 hover:text-slate-900 active:scale-98",
  btnDanger:
    "inline-flex items-center justify-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-100 transition-all",
  alertError: "rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-900",
  alertWarn: "rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs font-medium text-amber-900",
  segmentWrap: "flex gap-1 rounded-xl bg-slate-100 p-1",
  segmentActive: "bg-white text-slate-900 font-semibold shadow-xs rounded-lg transition-all",
  segmentIdle: "text-slate-600 hover:text-slate-900 rounded-lg transition-all",
} as const;
