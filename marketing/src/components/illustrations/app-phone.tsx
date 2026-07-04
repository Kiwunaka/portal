import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import { cn } from "../utils";

/**
 * Hand-drawn (CSS/SVG) POKROV connect screen in a phone frame.
 * No rasters: stays crisp on any display, inherits brand tokens.
 * Reference: current POKROV-app connect screen (ring + route row).
 */
export function AppPhoneIllustration({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "w-[280px] rounded-[2.25rem] border border-line bg-surface p-3 shadow-strong sm:w-[300px]",
        className,
      )}
    >
      <div className="flex flex-col gap-4 rounded-[1.75rem] bg-canvas px-5 pt-4 pb-6">
        {/* status bar */}
        <div className="flex items-center justify-between">
          <span className="text-[0.6875rem] font-semibold text-ink">9:41</span>
          <span className="flex gap-1">
            <span className="size-1.5 rounded-full bg-ink-muted" />
            <span className="size-1.5 rounded-full bg-ink-muted" />
            <span className="size-1.5 rounded-full bg-ink" />
          </span>
        </div>

        {/* app bar */}
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className="flex size-6 items-center justify-center rounded-lg bg-brand">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6 1.2 10 3v3.1c0 2.6-1.7 4.2-4 4.7-2.3-.5-4-2.1-4-4.7V3l4-1.8Z"
                  fill="#fff"
                  fillOpacity="0.92"
                />
              </svg>
            </span>
            <span className="text-[0.8125rem] font-bold tracking-[0.01em] text-ink">
              {CANONICAL_PLATFORM_BRAND}
            </span>
          </span>
          <span className="flex items-center gap-1.5 rounded-full bg-brand-soft px-2.5 py-1 text-[0.6875rem] font-semibold text-brand-strong">
            <span className="size-1.5 rounded-full bg-status-green" />
            Подключено
          </span>
        </div>

        {/* connect ring */}
        <div className="flex flex-col items-center gap-2 py-3">
          <div className="relative flex size-40 items-center justify-center rounded-full bg-[conic-gradient(var(--pokrov-status-green)_0deg,var(--pokrov-status-green)_310deg,var(--pokrov-accent-soft)_310deg)]">
            <div className="flex size-[8.25rem] flex-col items-center justify-center gap-1 rounded-full bg-surface shadow-soft">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2.5 19 5.6v5.2c0 4.5-3 7.4-7 8.4-4-1-7-3.9-7-8.4V5.6L12 2.5Z"
                  stroke="var(--pokrov-accent)"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                />
                <path
                  d="m8.8 11.6 2.2 2.2 4.2-4.4"
                  stroke="var(--pokrov-status-green)"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="text-[0.9375rem] font-bold text-ink">Подключено</span>
              <span className="max-w-[7rem] text-center text-[0.625rem] leading-tight text-ink-muted">
                нажмите, чтобы отключить
              </span>
            </div>
          </div>
        </div>

        {/* route row */}
        <div className="flex items-center justify-between rounded-(--radius-control) border border-line bg-surface px-4 py-3 shadow-soft">
          <span className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-full bg-brand-soft">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="5.4" stroke="var(--pokrov-accent)" strokeWidth="1.4" />
                <path d="M1.8 7h10.4M7 1.6c1.7 1.5 2.6 3.3 2.6 5.4S8.7 10.9 7 12.4C5.3 10.9 4.4 9.1 4.4 7S5.3 3.1 7 1.6Z" stroke="var(--pokrov-accent)" strokeWidth="1.2" />
              </svg>
            </span>
            <span className="flex flex-col">
              <span className="text-[0.8125rem] font-semibold text-ink">Авто</span>
              <span className="text-[0.6875rem] text-ink-muted">лучший маршрут</span>
            </span>
          </span>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="m5.2 3.5 3.6 3.5-3.6 3.5" stroke="var(--pokrov-text-muted)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        {/* bottom hint */}
        <div className="flex items-center justify-center gap-1.5 text-[0.6875rem] text-ink-muted">
          <span className="size-1.5 rounded-full bg-status-green" />
          защищённое подключение активно
        </div>
      </div>
    </div>
  );
}
