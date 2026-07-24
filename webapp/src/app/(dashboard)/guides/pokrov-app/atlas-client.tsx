"use client";

import { ChevronDown, Search, X } from "lucide-react";
import Image from "next/image";
import { useMemo, useState } from "react";

import {
  POKROV_ATLAS_CATEGORIES,
  POKROV_SCREEN_ATLAS,
  type PokrovAtlasScreen,
} from "../../../../../../shared/pokrov-screen-atlas";

const ALL = "Все";

function searchText(screen: PokrovAtlasScreen): string {
  return [
    screen.title,
    screen.category,
    screen.purpose,
    ...screen.path,
    ...(screen.recommendedSetup || []),
    screen.caution || "",
    ...screen.hotspots.flatMap((hotspot) => [
      hotspot.label,
      hotspot.action,
      hotspot.explanation,
      hotspot.recommendation || "",
    ]),
  ]
    .join(" ")
    .toLocaleLowerCase("ru");
}

export function CabinetPokrovAtlasClient() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(ALL);

  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ru");
    return POKROV_SCREEN_ATLAS.filter((screen) => {
      if (category !== ALL && screen.category !== category) return false;
      return !normalized || searchText(screen).includes(normalized);
    });
  }, [category, query]);

  return (
    <>
      <section className="rounded-card border border-line bg-surface p-4 shadow-soft">
        <label htmlFor="pokrov-atlas-search" className="text-sm font-bold text-ink">
          Найти экран или кнопку
        </label>
        <div className="relative mt-2">
          <Search
            size={18}
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-muted"
          />
          <input
            id="pokrov-atlas-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="WARP, DNS, код, тема, бонусы"
            className="min-h-12 w-full rounded-control border border-line bg-canvas py-2 pr-12 pl-10 text-base text-ink outline-none placeholder:text-ink-muted focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Очистить поиск"
              className="absolute top-1/2 right-1.5 grid size-10 -translate-y-1/2 place-items-center rounded-control text-ink-muted outline-none hover:bg-canvas-alt focus-visible:ring-2 focus-visible:ring-brand"
            >
              <X size={17} aria-hidden="true" />
            </button>
          ) : null}
        </div>
        <div
          className="mt-4 flex flex-wrap gap-2"
          role="group"
          aria-label="Категория экранов"
        >
          {[ALL, ...POKROV_ATLAS_CATEGORIES].map((item) => {
            const selected = category === item;
            const count =
              item === ALL
                ? POKROV_SCREEN_ATLAS.length
                : POKROV_SCREEN_ATLAS.filter(
                    (screen) => screen.category === item,
                  ).length;
            return (
              <button
                key={item}
                type="button"
                aria-pressed={selected}
                onClick={() => setCategory(item)}
                className={`min-h-11 rounded-full border px-3.5 py-2 text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 ${
                  selected
                    ? "border-brand bg-brand text-white"
                    : "border-line bg-canvas text-ink-muted hover:border-brand/50 hover:text-ink"
                }`}
              >
                {item}{" "}
                <span className={selected ? "text-white/75" : "text-ink-muted"}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <p className="text-sm text-ink-muted" aria-live="polite">
        Показано: <strong className="text-ink">{visible.length}</strong> из{" "}
        {POKROV_SCREEN_ATLAS.length}
      </p>

      <div className="grid gap-3">
        {visible.map((screen) => (
          <details
            key={screen.id}
            id={screen.id}
            className="group min-w-0 scroll-mt-24 rounded-card border border-line bg-surface p-4 shadow-soft"
          >
            <summary className="flex min-h-12 cursor-pointer list-none items-start justify-between gap-3 rounded-control outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2">
              <span className="flex min-w-0 items-start gap-3">
                <span className="grid size-9 shrink-0 place-items-center rounded-[12px] bg-brand text-xs font-black text-white">
                  {screen.order}
                </span>
                <span className="min-w-0">
                  <span className="block text-xs font-bold tracking-[0.08em] text-brand uppercase">
                    {screen.category} · {screen.path.join(" → ")}
                  </span>
                  <span className="mt-1 block text-base font-bold text-ink">
                    {screen.title}
                  </span>
                  <span className="mt-1 block text-sm leading-6 text-ink-muted">
                    {screen.purpose}
                  </span>
                </span>
              </span>
              <ChevronDown
                size={20}
                aria-hidden="true"
                className="mt-2 shrink-0 text-ink-muted transition-transform group-open:rotate-180"
              />
            </summary>

            <div className="mt-4 border-t border-line pt-4">
              {screen.recommendedSetup?.length ? (
                <section className="mb-3 rounded-control border border-brand/25 bg-brand-soft p-3.5">
                  <h2 className="text-sm font-bold text-ink">
                    Лучше настроить так
                  </h2>
                  <ul className="mt-2 grid list-disc gap-2 pl-5 text-sm leading-6 text-ink-soft">
                    {screen.recommendedSetup.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
              ) : null}

              <div className="relative overflow-hidden rounded-control border border-line bg-canvas-alt">
                <Image
                  src={screen.imageSrc}
                  alt={screen.imageAlt}
                  width={1920}
                  height={1080}
                  unoptimized
                  className="h-auto w-full"
                />
                {screen.hotspots.map((hotspot, index) => (
                  <div
                    key={hotspot.label}
                    aria-hidden="true"
                    className="pointer-events-none absolute rounded-[9px] border-[3px] border-[#ff3b30] shadow-[0_0_0_3px_rgba(255,255,255,0.92),0_0_0_6px_rgba(255,59,48,0.24)]"
                    style={{
                      left: `${hotspot.box.left}%`,
                      top: `${hotspot.box.top}%`,
                      width: `${hotspot.box.width}%`,
                      height: `${hotspot.box.height}%`,
                    }}
                  >
                    <span className="absolute -top-3 -left-3 grid size-6 place-items-center rounded-full border-2 border-white bg-[#ff3b30] text-[11px] font-black text-white shadow-lg">
                      {index + 1}
                    </span>
                  </div>
                ))}
              </div>

              <ol className="mt-3 grid gap-2">
                {screen.hotspots.map((hotspot, index) => (
                  <li
                    key={hotspot.label}
                    className="flex items-start gap-3 rounded-control border border-line bg-canvas-alt p-3"
                  >
                    <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[#ff3b30] text-xs font-black text-white">
                      {index + 1}
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-ink">
                        {hotspot.label}
                      </h3>
                      <p className="mt-1 text-sm leading-6 text-ink-soft">
                        <strong className="font-semibold text-ink">
                          Что нажать:
                        </strong>{" "}
                        {hotspot.action}
                      </p>
                      <p className="text-sm leading-6 text-ink-soft">
                        <strong className="font-semibold text-ink">
                          Что делает:
                        </strong>{" "}
                        {hotspot.explanation}
                      </p>
                      {hotspot.recommendation ? (
                        <p className="mt-1 text-sm leading-6 text-brand">
                          <strong>Лучше:</strong> {hotspot.recommendation}
                        </p>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>

              {screen.caution ? (
                <p className="mt-3 rounded-control border border-warn-line bg-warn-bg p-3 text-sm leading-6 text-warn-text">
                  <strong>Важно:</strong> {screen.caution}
                </p>
              ) : null}
            </div>
          </details>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="rounded-card border border-line bg-surface p-4 text-sm leading-6 text-ink-muted shadow-soft">
          Экран не найден. Сбросьте категорию или ищите по действию.
        </p>
      ) : null}
    </>
  );
}
