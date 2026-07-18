import { SkeletonBlock, SkeletonLine, SkeletonRegion } from "@/components/ui/skeleton";

/**
 * Route-level cold-start fallback. Mirrors the persistent cabinet shell so a
 * hard load paints one stable, server-renderable skeleton without client hooks.
 * This stays a div because the streamed page owns the document's main landmark.
 */
export default function Loading() {
  return (
    <div
      className="mx-auto w-full max-w-[1400px] px-3 py-4 sm:px-4 lg:px-5"
      style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}
    >
      <SkeletonRegion label="Открываем кабинет POKROV">
        <div className="grid min-h-[calc(100dvh-2rem)] gap-4 lg:grid-cols-[252px_1fr]">
          <aside className="hidden rounded-panel border border-line bg-surface p-4 shadow-soft lg:block">
            <SkeletonLine className="h-11 w-36" />
            <div className="mt-5 space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <SkeletonBlock key={index} className="h-[52px]" />
              ))}
            </div>
          </aside>

          <section className="min-w-0 pb-[calc(2rem+var(--tg-safe-area-bottom,0px))] lg:pb-8">
            <div className="mx-auto w-full max-w-[760px] space-y-4">
              <p className="text-sm font-semibold text-ink-soft">Открываем кабинет — проверяем сессию и данные доступа.</p>
              <SkeletonBlock className="h-32" />
              <SkeletonBlock className="h-44" />
              <SkeletonBlock className="h-32" />
            </div>
          </section>
        </div>
      </SkeletonRegion>
    </div>
  );
}
