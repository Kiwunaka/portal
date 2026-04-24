export default function Loading() {
  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-6xl items-center px-4 py-8 sm:px-6" aria-busy="true" aria-live="polite">
      <section className="w-full rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-800 dark:text-emerald-200">
              Открываем кабинет
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,4vw,3rem)] font-semibold leading-[0.98] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              Подтягиваем ваш контекст
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
              Проверяем сессию, срок доступа и связанные устройства. Если данных пока нет, экран честно покажет пустое состояние.
            </p>
          </div>
          <div className="h-12 w-12 rounded-[18px] border border-emerald-200 bg-emerald-50 p-2 dark:border-emerald-400/20 dark:bg-emerald-400/10">
            <div className="h-full w-full animate-pulse rounded-xl bg-emerald-700/70 dark:bg-emerald-300/70" />
          </div>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-[1.6rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            <div className="h-3 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
            <div className="mt-4 h-12 w-full max-w-xl animate-pulse rounded-[1.2rem] bg-slate-200 dark:bg-white/10" />
            <div className="mt-4 h-4 w-full animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
            <div className="mt-3 h-4 w-4/5 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
            <div className="mt-5 flex flex-wrap gap-3">
              <div className="h-11 w-36 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="h-11 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
            </div>
          </div>
          <div className="grid gap-3">
            <div className="h-28 animate-pulse rounded-[1.35rem] border border-slate-200/80 bg-slate-50/90 dark:border-white/10 dark:bg-white/[0.04]" />
            <div className="h-28 animate-pulse rounded-[1.35rem] border border-slate-200/80 bg-slate-50/90 dark:border-white/10 dark:bg-white/[0.04]" />
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {["Срок", "Устройства", "Поддержка"].map((label) => (
            <div key={label} className="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
              <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{label}</p>
              <div className="mt-3 h-7 w-3/4 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
