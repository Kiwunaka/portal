import { cn } from "../utils";

export type StepMiniVariant = "download" | "connect" | "done" | "android-permission" | "windows-smartscreen";

function DownloadMini() {
  return (
    <div className="flex w-44 flex-col gap-2.5 rounded-(--radius-control) border border-line bg-surface p-3.5 shadow-soft">
      <div className="flex items-center gap-2">
        <span className="flex size-7 items-center justify-center rounded-lg bg-brand-soft">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M7 1.8v7m0 0L4.2 6m2.8 2.8L9.8 6M2.2 11.4h9.6" stroke="var(--pokrov-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <span className="flex flex-col">
          <span className="text-[0.6875rem] font-semibold text-ink">pokrov-setup</span>
          <span className="text-[0.5625rem] text-ink-soft">загружается…</span>
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-canvas-alt">
        <div className="h-full w-3/4 rounded-full bg-brand" />
      </div>
    </div>
  );
}

function ConnectMini() {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex size-20 items-center justify-center rounded-full bg-brand shadow-[0_0_0_10px_var(--pokrov-accent-soft)]">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 3v8" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
          <path d="M7.5 6.4a7 7 0 1 0 9 0" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      <span className="text-[0.6875rem] font-semibold text-ink">одно касание</span>
    </div>
  );
}

function DoneMini() {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex size-20 items-center justify-center rounded-full bg-[conic-gradient(var(--pokrov-status-green)_0deg,var(--pokrov-status-green)_360deg)]">
        <div className="flex size-16 items-center justify-center rounded-full bg-surface">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path d="m6 12.5 4 4 8-9" stroke="var(--pokrov-status-green)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
      <span className="flex items-center gap-1.5 text-[0.6875rem] font-semibold text-ink">
        <span className="size-1.5 rounded-full bg-status-green" />
        Подключено
      </span>
    </div>
  );
}

function AndroidPermissionMini() {
  return (
    <div className="flex w-48 flex-col gap-2.5 rounded-(--radius-control) border border-line bg-surface p-3.5 shadow-soft">
      <span className="text-[0.6875rem] font-semibold text-ink">Установка приложения</span>
      <span className="text-[0.5625rem] leading-snug text-ink-soft">
        Разрешить установку из этого источника?
      </span>
      <div className="flex justify-end gap-2">
        <span className="rounded-full px-2.5 py-1 text-[0.5625rem] font-semibold text-ink-soft">Отмена</span>
        <span className="rounded-full bg-brand-strong px-2.5 py-1 text-[0.5625rem] font-semibold text-ink-inverse">
          Разрешить
        </span>
      </div>
    </div>
  );
}

function WindowsSmartscreenMini() {
  return (
    <div className="flex w-48 flex-col gap-2 rounded-(--radius-control) border border-line bg-surface p-3.5 shadow-soft">
      <span className="flex items-center gap-1.5 text-[0.6875rem] font-semibold text-ink">
        <svg width="11" height="11" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M7 1.5 12.5 3v4c0 3.2-2.2 5.3-5.5 6-3.3-.7-5.5-2.8-5.5-6V3L7 1.5Z" stroke="var(--pokrov-accent)" strokeWidth="1.3" strokeLinejoin="round" />
        </svg>
        Windows защитил ваш компьютер
      </span>
      <span className="text-[0.5625rem] leading-snug text-ink-soft">
        Подробнее → «Выполнить в любом случае»
      </span>
      <div className="flex justify-end gap-2">
        <span className="rounded-full border border-line px-2.5 py-1 text-[0.5625rem] font-semibold text-ink">
          Выполнить
        </span>
      </div>
    </div>
  );
}

/** Mini illustrative screens for onboarding / install steps (CSS/SVG, no rasters). */
export function StepMiniIllustration({ className, variant }: { className?: string; variant: StepMiniVariant }) {
  return (
    <div aria-hidden="true" className={cn("flex items-center justify-center", className)}>
      {variant === "download" ? (
        <DownloadMini />
      ) : variant === "connect" ? (
        <ConnectMini />
      ) : variant === "done" ? (
        <DoneMini />
      ) : variant === "android-permission" ? (
        <AndroidPermissionMini />
      ) : (
        <WindowsSmartscreenMini />
      )}
    </div>
  );
}
