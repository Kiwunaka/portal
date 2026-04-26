export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8" aria-busy="true" aria-live="polite">
      <div className="grid gap-4 lg:grid-cols-[260px,1fr]">
        <aside className="glass-card hidden p-5 lg:block">
          <div className="h-4 w-24 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
          <div className="mt-6 space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-11 animate-pulse rounded-2xl bg-slate-200 dark:bg-white/10" />
            ))}
          </div>
        </aside>

        <div className="glass-card overflow-hidden p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-emerald-700 dark:text-emerald-300">РѕС‚РєСЂС‹РІР°РµРј РєР°Р±РёРЅРµС‚</p>
          <h1 className="mt-3 font-display text-3xl font-bold text-slate-900 dark:text-white">POKROV СѓР¶Рµ РїРѕРґРіСЂСѓР¶Р°РµС‚ РІР°С€ РєРѕРЅС‚РµРєСЃС‚</h1>
          <p className="mt-3 max-w-2xl text-sm text-slate-600 dark:text-slate-300">
            РћР±С‰Р°СЏ РѕР±РѕР»РѕС‡РєР° РєР°Р±РёРЅРµС‚Р° РѕСЃС‚Р°С‘С‚СЃСЏ РЅР° РјРµСЃС‚Рµ, РїРѕРєР° РїРѕРґС‚СЏРіРёРІР°СЋС‚СЃСЏ РґР°РЅРЅС‹Рµ РїРѕ РґРѕСЃС‚СѓРїСѓ Рё СѓСЃС‚СЂРѕР№СЃС‚РІР°Рј.
          </p>
          <div className="mt-6 grid gap-4 lg:grid-cols-[1.6fr,1fr]">
            <div className="space-y-3 rounded-2xl border border-white/45 bg-white/65 p-5 dark:border-white/10 dark:bg-white/5">
              <div className="h-3 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="h-10 w-full max-w-xl animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="h-4 w-full animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="h-4 w-5/6 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="mt-4 flex flex-wrap gap-3">
                <div className="h-11 w-36 animate-pulse rounded-xl bg-slate-200 dark:bg-white/10" />
                <div className="h-11 w-36 animate-pulse rounded-xl bg-slate-200 dark:bg-white/10" />
              </div>
            </div>
            <div className="grid gap-3">
              <div className="h-28 animate-pulse rounded-2xl border border-white/45 bg-white/65 dark:border-white/10 dark:bg-white/5" />
              <div className="h-28 animate-pulse rounded-2xl border border-white/45 bg-white/65 dark:border-white/10 dark:bg-white/5" />
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-2xl border border-white/45 bg-white/65 dark:border-white/10 dark:bg-white/5" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
