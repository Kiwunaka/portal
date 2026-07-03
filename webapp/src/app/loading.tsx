export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8" aria-busy="true" aria-live="polite">
      <div className="grid gap-4 lg:grid-cols-[260px,1fr]">
        <aside className="glass-card hidden p-5 lg:block">
          <div className="h-4 w-24 motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-border)]" />
          <div className="mt-6 space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-11 motion-safe:animate-pulse rounded-2xl bg-[color:var(--atlas-border)]" />
            ))}
          </div>
        </aside>

        <div className="glass-card overflow-hidden p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-[color:var(--atlas-status-success-text)]">Открываем кабинет</p>
          <h1 className="mt-3 font-display text-3xl font-bold text-[color:var(--atlas-text)]">POKROV готовит рабочее пространство</h1>
          <p className="mt-3 max-w-2xl text-sm text-[color:var(--atlas-text-soft)]">
            Обновляем данные по доступу и устройствам. Оболочка кабинета останется на месте после первого входа.
          </p>
          <div className="mt-6 grid gap-4 lg:grid-cols-[1.6fr,1fr]">
            <div className="space-y-3 rounded-2xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5">
              <div className="h-3 w-32 motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-border)]" />
              <div className="h-10 w-full max-w-xl motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-border)]" />
              <div className="h-4 w-full motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-border)]" />
              <div className="h-4 w-5/6 motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-border)]" />
              <div className="mt-4 flex flex-wrap gap-3">
                <div className="h-11 w-36 motion-safe:animate-pulse rounded-xl bg-[color:var(--atlas-border)]" />
                <div className="h-11 w-36 motion-safe:animate-pulse rounded-xl bg-[color:var(--atlas-border)]" />
              </div>
            </div>
            <div className="grid gap-3">
              <div className="h-28 motion-safe:animate-pulse rounded-2xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]" />
              <div className="h-28 motion-safe:animate-pulse rounded-2xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]" />
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-24 motion-safe:animate-pulse rounded-2xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
