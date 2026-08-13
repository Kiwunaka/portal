"use client";

import { CheckCircle2, ChevronDown, Search, X } from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import {
  POKROV_ATLAS_CATEGORIES,
  POKROV_SCREEN_ATLAS,
  type PokrovAtlasScreen,
} from "../../../../../shared/pokrov-screen-atlas";

const ALL = "Все";

function screenSearchText(screen: PokrovAtlasScreen): string {
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

export function PokrovAtlasClient() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(ALL);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (!id || !POKROV_SCREEN_ATLAS.some((screen) => screen.id === id)) return;
    const frame = window.requestAnimationFrame(() => {
      setExpanded(new Set([id]));
      window.requestAnimationFrame(() => {
        document.getElementById(id)?.scrollIntoView({ block: "start" });
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ru");
    return POKROV_SCREEN_ATLAS.filter((screen) => {
      if (category !== ALL && screen.category !== category) return false;
      return !normalized || screenSearchText(screen).includes(normalized);
    });
  }, [category, query]);

  const allVisibleExpanded =
    visible.length > 0 && visible.every((screen) => expanded.has(screen.id));

  function toggleAll() {
    setExpanded((current) => {
      const next = new Set(current);
      if (allVisibleExpanded) {
        visible.forEach((screen) => next.delete(screen.id));
      } else {
        visible.forEach((screen) => next.add(screen.id));
      }
      return next;
    });
  }

  function setScreenExpanded(id: string, open: boolean) {
    setExpanded((current) => {
      const next = new Set(current);
      if (open) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-panel border border-line bg-surface p-4">
        <label
          htmlFor="atlas-search"
          className="text-sm font-semibold text-ink"
        >
          Найти экран, кнопку или настройку
        </label>
        <div className="relative mt-2">
          <Search
            size={19}
            strokeWidth={2}
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-muted"
          />
          <input
            id="atlas-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Например: WARP, код, DNS, избранное или тема"
            className="min-h-12 w-full rounded-[12px] border border-line bg-canvas py-2 pr-12 pl-10 text-base text-ink outline-none placeholder:text-ink-soft focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Очистить поиск"
              className="absolute top-1/2 right-1.5 grid size-10 -translate-y-1/2 place-items-center rounded-[10px] text-ink-soft outline-none hover:bg-canvas-alt focus-visible:ring-2 focus-visible:ring-brand"
            >
              <X size={18} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div
          className="mt-4 flex flex-wrap gap-2"
          role="group"
          aria-label="Категория экранов POKROV"
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
                className={`min-h-11 rounded-full border px-3.5 py-2 text-sm font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 ${
                  selected
                    ? "border-brand bg-brand text-white"
                    : "border-line bg-canvas text-ink-soft hover:border-brand/50 hover:text-ink"
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

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-soft" aria-live="polite">
          Показано: <strong className="text-ink">{visible.length}</strong> из{" "}
          {POKROV_SCREEN_ATLAS.length}
        </p>
        <button
          type="button"
          onClick={toggleAll}
          disabled={visible.length === 0}
          className="min-h-11 rounded-[12px] border border-line bg-surface px-4 text-sm font-semibold text-ink outline-none hover:border-brand/50 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-brand"
        >
          {allVisibleExpanded ? "Свернуть найденное" : "Развернуть найденное"}
        </button>
      </div>

      <div className="grid gap-4">
        {visible.map((screen) => {
          const open = expanded.has(screen.id);
          return (
            <details
              key={screen.id}
              id={screen.id}
              open={open}
              className="group scroll-mt-24 rounded-panel border border-line bg-surface shadow-[0_16px_44px_rgba(15,23,42,0.07)]"
            >
              <summary
                onClick={(event) => {
                  event.preventDefault();
                  setScreenExpanded(screen.id, !open);
                }}
                className="flex min-h-20 cursor-pointer list-none items-start justify-between gap-4 rounded-panel p-4 outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset sm:p-5"
              >
                <span className="flex min-w-0 items-start gap-3">
                  <span className="grid size-10 shrink-0 place-items-center rounded-[13px] bg-brand text-sm font-black text-white">
                    {screen.order}
                  </span>
                  <span>
                    <span className="block text-xs font-bold tracking-[0.08em] text-brand uppercase">
                      {screen.category} · {screen.path.join(" → ")}
                    </span>
                    <span className="mt-1 block font-display text-lg font-bold text-ink sm:text-xl">
                      {screen.title}
                    </span>
                    <span className="mt-1 block text-sm leading-6 text-ink-soft">
                      {screen.purpose}
                    </span>
                  </span>
                </span>
                <ChevronDown
                  size={22}
                  aria-hidden="true"
                  className="mt-2 shrink-0 text-ink-muted transition-transform group-open:rotate-180"
                />
              </summary>

              <div className="border-t border-line p-4 sm:p-5">
                {screen.recommendedSetup?.length ? (
                  <section className="mb-4 rounded-control border border-brand/25 bg-brand-soft p-4">
                    <h2 className="text-sm font-bold text-ink">
                      Лучше настроить так
                    </h2>
                    <ul className="mt-2 grid gap-2 text-sm leading-6 text-ink-soft">
                      {screen.recommendedSetup.map((item) => (
                        <li key={item} className="flex items-start gap-2">
                          <CheckCircle2
                            size={17}
                            strokeWidth={2}
                            aria-hidden="true"
                            className="mt-1 shrink-0 text-brand"
                          />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                <div className="relative overflow-hidden rounded-[18px] border border-line bg-[#eef2f0]">
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
                      className="pointer-events-none absolute rounded-[10px] border-[3px] border-[#ff3b30] shadow-[0_0_0_3px_rgba(255,255,255,0.92),0_0_0_6px_rgba(255,59,48,0.24)]"
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

                <ol className="mt-4 grid gap-3">
                  {screen.hotspots.map((hotspot, index) => (
                    <li
                      key={hotspot.label}
                      className="flex items-start gap-3 rounded-control border border-line bg-canvas-alt p-3.5"
                    >
                      <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[#ff3b30] text-xs font-black text-white">
                        {index + 1}
                      </span>
                      <div className="min-w-0">
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
                  <p className="mt-4 rounded-control border border-[#f0c36d] bg-[#fff8e8] p-3.5 text-sm leading-6 text-[#6f4d08]">
                    <strong>Важно:</strong> {screen.caution}
                  </p>
                ) : null}
              </div>
            </details>
          );
        })}
      </div>

      {visible.length === 0 ? (
        <p className="rounded-panel border border-line bg-surface p-5 text-sm leading-6 text-ink-soft">
          Экран не найден. Сбросьте категорию или ищите по названию действия:
          «подключить», «код», «DNS», «тема», «бонусы».
        </p>
      ) : null}
    </div>
  );
}
