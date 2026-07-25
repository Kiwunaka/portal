import Image from "next/image";

import {
  GUIDE_VISUALS,
  type GuideVisualScreenshot,
  type GuideVisualSpec,
} from "../../../../shared/guide-visuals";

function Simulation({ visual }: { visual: GuideVisualSpec }) {
  const narrow = visual.device === "phone";
  return (
    <div
      className={`mx-auto overflow-hidden border border-line bg-canvas shadow-[0_18px_50px_rgba(15,23,42,0.12)] ${
        narrow
          ? "w-full max-w-[280px] rounded-[28px]"
          : "w-full rounded-[18px]"
      }`}
    >
      <div className="flex items-center gap-1.5 border-b border-line bg-ink px-3 py-2">
        <span className="size-2 rounded-full bg-[#ff5f57]" />
        <span className="size-2 rounded-full bg-[#febc2e]" />
        <span className="size-2 rounded-full bg-[#28c840]" />
        <span className="ml-2 truncate text-[10px] font-semibold tracking-[0.08em] text-white/70 uppercase">
          {visual.client} · {visual.screen}
        </span>
      </div>
      <div className="bg-[radial-gradient(circle_at_top_right,rgba(50,116,229,0.16),transparent_42%)] p-4">
        <div className="mb-3">
          <p className="text-[10px] font-bold tracking-[0.12em] text-brand uppercase">
            Экран
          </p>
          <p className="mt-0.5 text-sm font-bold text-ink">{visual.screen}</p>
        </div>
        <div className="grid gap-2">
          {visual.path.map((item, index) => {
            const target = index === 1;
            return (
              <div
                key={item}
                className={`relative flex min-h-11 items-center gap-3 rounded-[12px] border px-3 py-2.5 text-sm ${
                  target
                    ? "border-brand bg-brand-soft text-ink ring-2 ring-brand/25"
                    : "border-line bg-surface text-ink-soft"
                }`}
              >
                <span
                  className={`grid size-6 shrink-0 place-items-center rounded-full text-xs font-bold ${
                    target
                      ? "bg-brand text-white"
                      : "bg-canvas-alt text-ink-muted"
                  }`}
                >
                  {index + 1}
                </span>
                <span className={target ? "font-bold" : "font-medium"}>
                  {item}
                </span>
                {target ? (
                  <span className="ml-auto shrink-0 rounded-full bg-brand px-2 py-1 text-[10px] font-bold text-white uppercase">
                    Нажать
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function screenshotsFor(visual: GuideVisualSpec): readonly GuideVisualScreenshot[] {
  if (visual.screenshots?.length) return visual.screenshots;
  if (!visual.imageSrc) return [];
  return [
    {
      imageSrc: visual.imageSrc,
      imageAlt: visual.imageAlt || `${visual.client}: ${visual.screen}`,
      imageWidth: visual.imageWidth || 1738,
      imageHeight: visual.imageHeight || 1420,
      title: visual.screen,
      instruction: visual.hotspot?.label || visual.path[1],
      hotspot: visual.hotspot,
    },
  ];
}

function ScreenshotGallery({ visual }: { visual: GuideVisualSpec }) {
  const screenshots = screenshotsFor(visual);
  if (screenshots.length === 0) return <Simulation visual={visual} />;

  const columns =
    screenshots.length === 1
      ? ""
      : screenshots.length === 2
        ? "sm:grid-cols-2"
        : screenshots.length === 3
          ? "sm:grid-cols-2 lg:grid-cols-3"
          : "sm:grid-cols-2";

  return (
    <div className={`grid gap-3 ${columns}`}>
      {screenshots.map((screenshot, index) => (
        <figure
          key={screenshot.imageSrc}
          className="min-w-0 rounded-[16px] border border-line bg-surface p-3"
        >
          <div className="flex items-start gap-2.5">
            <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[#ff3b30] text-xs font-black text-white">
              {index + 1}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-bold text-ink">{screenshot.title}</p>
              <p className="mt-0.5 text-xs leading-5 text-ink-soft">
                {screenshot.instruction}
              </p>
            </div>
          </div>

          <div className="mt-3 flex justify-center overflow-hidden rounded-[12px] bg-[#111217]">
            <div className="relative inline-block max-w-full">
              <Image
                src={screenshot.imageSrc}
                alt={screenshot.imageAlt}
                width={screenshot.imageWidth}
                height={screenshot.imageHeight}
                unoptimized
                className="h-auto max-h-[560px] w-auto max-w-full object-contain"
              />
              {screenshot.hotspot ? (
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute rounded-[9px] border-[3px] border-[#ff3b30] shadow-[0_0_0_3px_rgba(255,255,255,0.92),0_0_0_6px_rgba(255,59,48,0.28)]"
                  style={{
                    left: `${screenshot.hotspot.left}%`,
                    top: `${screenshot.hotspot.top}%`,
                    width: `${screenshot.hotspot.width}%`,
                    height: `${screenshot.hotspot.height}%`,
                  }}
                >
                  <span className="absolute -top-3 -left-3 grid size-6 place-items-center rounded-full border-2 border-white bg-[#ff3b30] text-[11px] font-black text-white shadow-lg">
                    {index + 1}
                  </span>
                </div>
              ) : null}
            </div>
          </div>
        </figure>
      ))}
    </div>
  );
}

export function GuideVisual({ guideId }: { guideId: string }) {
  const visual = GUIDE_VISUALS[guideId];
  if (!visual) return null;

  return (
    <section
      className="rounded-[18px] border border-line bg-canvas-alt p-3.5"
      aria-label={`Визуальная инструкция: ${visual.client}, ${visual.screen}`}
      data-testid={`guide-visual-${guideId}`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-ink px-2.5 py-1 text-[10px] font-bold tracking-[0.08em] text-white uppercase">
          {visual.client}
        </span>
        <span className="rounded-full border border-line bg-surface px-2.5 py-1 text-[10px] font-semibold text-ink-soft">
          {visual.platform}
        </span>
        <span className="text-xs font-semibold text-ink-soft">
          {visual.screen}
        </span>
      </div>

      {visual.kind === "screenshot" ? (
        <ScreenshotGallery visual={visual} />
      ) : (
        <Simulation visual={visual} />
      )}

      {visual.kind === "simulation" ? (
        <p className="mt-3 text-xs leading-5 text-ink-soft">
          <strong className="text-ink">Куда нажать:</strong> {visual.path[1]}
        </p>
      ) : null}
      {visual.note ? (
        <p className="mt-3 text-xs leading-5 text-ink-muted">{visual.note}</p>
      ) : null}
      {visual.sources?.length || visual.sourceHref ? (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {(
            visual.sources ||
            (visual.sourceHref
              ? [
                  {
                    href: visual.sourceHref,
                    label: visual.sourceLabel || "Источник",
                  },
                ]
              : [])
          ).map((source) => (
            <a
              key={source.href}
              href={source.href}
              target="_blank"
              rel="noreferrer"
              className="inline-flex text-xs font-semibold text-brand underline decoration-brand/30 underline-offset-4 hover:decoration-brand"
            >
              {source.label}
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}
