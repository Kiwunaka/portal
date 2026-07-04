import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import { cn } from "../utils";

/**
 * Hand-drawn POKROV Windows client frame (CSS/SVG, no rasters).
 * Simplified: title bar, sidebar, connect state.
 */
export function AppWindowIllustration({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "w-full max-w-md overflow-hidden rounded-(--radius-card) border border-line bg-surface shadow-strong",
        className,
      )}
    >
      {/* title bar */}
      <div className="flex items-center justify-between border-b border-line bg-canvas-alt px-4 py-2.5">
        <span className="flex items-center gap-2">
          <span className="flex size-4.5 items-center justify-center rounded bg-brand">
            <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M6 1.2 10 3v3.1c0 2.6-1.7 4.2-4 4.7-2.3-.5-4-2.1-4-4.7V3l4-1.8Z" fill="#fff" fillOpacity="0.92" />
            </svg>
          </span>
          <span className="text-[0.6875rem] font-semibold text-ink">{CANONICAL_PLATFORM_BRAND}</span>
        </span>
        <span className="flex items-center gap-2.5 text-ink-muted">
          <svg width="9" height="9" viewBox="0 0 10 10"><path d="M1 5h8" stroke="currentColor" strokeWidth="1.2" /></svg>
          <svg width="9" height="9" viewBox="0 0 10 10"><rect x="1.5" y="1.5" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" /></svg>
          <svg width="9" height="9" viewBox="0 0 10 10"><path d="m1.5 1.5 7 7m0-7-7 7" stroke="currentColor" strokeWidth="1.2" /></svg>
        </span>
      </div>

      <div className="flex">
        {/* sidebar */}
        <div className="flex w-32 flex-col gap-1 border-r border-line bg-canvas-alt p-2.5">
          <span className="rounded-lg bg-brand-soft px-2.5 py-1.5 text-[0.6875rem] font-semibold text-brand-strong">
            Подключение
          </span>
          <span className="px-2.5 py-1.5 text-[0.6875rem] text-ink-soft">Маршруты</span>
          <span className="px-2.5 py-1.5 text-[0.6875rem] text-ink-soft">Аккаунт</span>
          <span className="px-2.5 py-1.5 text-[0.6875rem] text-ink-soft">Настройки</span>
        </div>

        {/* content */}
        <div className="flex flex-1 flex-col items-center gap-3 px-6 py-7">
          <div className="relative flex size-24 items-center justify-center rounded-full bg-[conic-gradient(var(--pokrov-status-green)_0deg,var(--pokrov-status-green)_310deg,var(--pokrov-accent-soft)_310deg)]">
            <div className="flex size-[4.75rem] flex-col items-center justify-center rounded-full bg-surface shadow-soft">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M12 2.5 19 5.6v5.2c0 4.5-3 7.4-7 8.4-4-1-7-3.9-7-8.4V5.6L12 2.5Z" stroke="var(--pokrov-accent)" strokeWidth="1.8" strokeLinejoin="round" />
                <path d="m8.8 11.6 2.2 2.2 4.2-4.4" stroke="var(--pokrov-status-green)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="text-[0.6875rem] font-bold text-ink">Подключено</span>
            </div>
          </div>
          <span className="flex items-center gap-1.5 text-[0.6875rem] text-ink-muted">
            <span className="size-1.5 rounded-full bg-status-green" />
            Авто · лучший маршрут
          </span>
        </div>
      </div>
    </div>
  );
}
