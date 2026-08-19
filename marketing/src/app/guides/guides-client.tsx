"use client";

import { BookOpenCheck, ChevronDown, Search, X } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { POKROV_SCREEN_ATLAS } from "../../../../shared/pokrov-screen-atlas";
import {
  USER_GUIDE_DETAILS,
  USER_GUIDES,
  type UserGuideDetail,
} from "../../../../shared/trust-and-guides";
import { Card } from "../../components/ui/card";
import { GuideVisual } from "./guide-visual";

const ALL = "Все";

function detailSearchText(detail: UserGuideDetail | undefined): string[] {
  if (!detail) return [];
  return [
    ...detail.steps,
    ...detail.failure_steps,
    ...(detail.recommended_setup || []),
    ...(detail.warnings || []),
    ...(detail.controls || []).flatMap((control) => [
      control.label,
      control.does,
      control.use_when,
    ]),
  ];
}

function atlasSearchText(screen: (typeof POKROV_SCREEN_ATLAS)[number]): string {
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

export function GuidesClient() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(ALL);

  const categories = useMemo(() => {
    const values = Array.from(
      new Set(USER_GUIDES.map((guide) => guide.category)),
    );
    return [
      { label: ALL, count: USER_GUIDES.length },
      ...values.map((label) => ({
        label,
        count: USER_GUIDES.filter((guide) => guide.category === label).length,
      })),
    ];
  }, []);

  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ru");
    return USER_GUIDES.filter((guide) => {
      if (category !== ALL && guide.category !== category) return false;
      if (!normalized) return true;
      const detail = USER_GUIDE_DETAILS[guide.id];
      return [
        guide.title,
        guide.category,
        guide.platform,
        guide.prerequisites,
        guide.expected,
        guide.failure,
        ...detailSearchText(detail),
      ]
        .join(" ")
        .toLocaleLowerCase("ru")
        .includes(normalized);
    });
  }, [category, query]);

  const atlasMatches = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ru");
    if (!normalized || category !== ALL) return [];
    return POKROV_SCREEN_ATLAS.filter((screen) =>
      atlasSearchText(screen).includes(normalized),
    );
  }, [category, query]);

  return (
    <>
      <Link
        href="/guides/pokrov-app/"
        className="group flex min-h-24 items-start gap-3 rounded-panel border border-brand/30 bg-brand-soft p-4 outline-none transition-colors hover:border-brand focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-[14px] bg-brand text-white">
          <BookOpenCheck size={22} strokeWidth={2} aria-hidden="true" />
        </span>
        <span>
          <span className="block text-xs font-bold tracking-[0.08em] text-brand uppercase">
            Отдельный атлас · {POKROV_SCREEN_ATLAS.length} экрана
          </span>
          <span className="mt-1 block font-display text-lg font-bold text-ink">
            Весь POKROV: что делает каждая кнопка
          </span>
          <span className="mt-1 block text-sm leading-6 text-ink-soft">
            Реальные снимки Android, точные обводки, порядок настройки и
            предупреждения для каждого основного экрана и панели.
          </span>
        </span>
      </Link>

      <div className="rounded-panel border border-line bg-surface p-4">
        <label
          htmlFor="guide-search"
          className="text-sm font-semibold text-ink"
        >
          Поиск по задаче, кнопке или клиенту
        </label>
        <div className="relative mt-2">
          <Search
            size={19}
            strokeWidth={2}
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-muted"
          />
          <input
            id="guide-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Например: Happ JSON, Android TV, DNS или продление"
            className="min-h-12 w-full rounded-[12px] border border-line bg-canvas py-2 pr-12 pl-10 text-base font-normal text-ink outline-none placeholder:text-ink-soft focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Очистить поиск"
              className="absolute top-1/2 right-1.5 grid size-10 -translate-y-1/2 place-items-center rounded-[10px] text-ink-soft outline-none hover:bg-canvas-alt hover:text-ink focus-visible:ring-2 focus-visible:ring-brand"
            >
              <X size={18} strokeWidth={2} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div className="mt-4">
          <p className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">
            Категории
          </p>
          <div
            className="mt-2 flex flex-wrap gap-2"
            role="group"
            aria-label="Фильтр по категории"
          >
            {categories.map((item) => {
              const selected = item.label === category;
              return (
                <button
                  key={item.label}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => setCategory(item.label)}
                  className={`min-h-11 rounded-full border px-3.5 py-2 text-sm font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 ${
                    selected
                      ? "border-brand bg-brand text-white"
                      : "border-line bg-canvas text-ink-soft hover:border-brand/50 hover:text-ink"
                  }`}
                >
                  {item.label}{" "}
                  <span className={selected ? "text-white/75" : "text-ink-muted"}>
                    {item.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div
        className="flex flex-wrap items-center justify-between gap-2"
        aria-live="polite"
      >
        <p className="text-sm text-ink-soft">
          Найдено: <strong className="text-ink">{visible.length}</strong>
        </p>
        {category !== ALL || query ? (
          <button
            type="button"
            onClick={() => {
              setCategory(ALL);
              setQuery("");
            }}
            className="min-h-11 rounded-[12px] px-3 text-sm font-semibold text-brand outline-none hover:bg-brand-soft focus-visible:ring-2 focus-visible:ring-brand"
          >
            Сбросить фильтры
          </button>
        ) : null}
      </div>

      {atlasMatches.length ? (
        <section className="rounded-panel border border-brand/30 bg-brand-soft p-4">
          <p className="text-xs font-bold tracking-[0.08em] text-brand uppercase">
            Найдено в атласе экранов · {atlasMatches.length}
          </p>
          <div className="mt-2 grid gap-2">
            {atlasMatches.slice(0, 3).map((screen) => (
              <Link
                key={screen.id}
                href={`/guides/pokrov-app/#${screen.id}`}
                className="flex min-h-11 items-center justify-between gap-3 rounded-[12px] border border-line bg-surface px-3.5 py-2.5 text-sm font-semibold text-ink outline-none hover:border-brand/50 focus-visible:ring-2 focus-visible:ring-brand"
              >
                <span>{screen.title}</span>
                <span className="shrink-0 text-brand">Открыть</span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <div className="grid gap-4">
        {visible.map((guide) => {
          const detail = USER_GUIDE_DETAILS[guide.id];
          return (
            <details
              key={guide.id}
              id={guide.id}
              className="group min-w-0 scroll-mt-24 rounded-panel border border-line bg-surface shadow-[0_14px_38px_rgba(15,23,42,0.06)]"
            >
              <summary className="flex min-h-24 cursor-pointer list-none items-start justify-between gap-3 rounded-panel p-4 outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset sm:p-5">
                <span className="min-w-0">
                  <span className="block text-xs font-semibold tracking-[0.08em] text-brand uppercase">
                    {guide.category} · {guide.platform}
                  </span>
                  <span className="mt-1 block font-display text-lg font-bold text-ink sm:text-xl">
                    {guide.title}
                  </span>
                  <span className="mt-1 line-clamp-2 block text-sm leading-6 text-ink-soft">
                    {guide.expected}
                  </span>
                </span>
                <ChevronDown
                  size={22}
                  aria-hidden="true"
                  className="mt-2 shrink-0 text-ink-muted transition-transform group-open:rotate-180"
                />
              </summary>

              <div className="grid gap-4 border-t border-line p-4 sm:p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold tracking-[0.08em] text-brand uppercase">
                      Подробная инструкция
                    </p>
                    <h2 className="mt-1 font-display text-xl font-bold text-ink sm:text-2xl">
                      {guide.title}
                    </h2>
                  </div>
                  <span className="rounded-full border border-line bg-canvas-alt px-2.5 py-1 text-xs font-semibold text-ink-soft">
                    {guide.video === "planned" ? "Видео готовится" : "Видео"}
                  </span>
                </div>

                <dl className="grid gap-3 text-sm leading-relaxed sm:grid-cols-2">
                  <div>
                    <dt className="font-semibold text-ink">Перед началом</dt>
                    <dd className="text-ink-soft">{guide.prerequisites}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink">Проверено</dt>
                    <dd className="text-ink-soft">
                      {detail?.last_verified || "Требует проверки"}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink">Результат</dt>
                    <dd className="text-ink-soft">{guide.expected}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink">
                      Если не получилось
                    </dt>
                    <dd className="text-ink-soft">{guide.failure}</dd>
                  </div>
                </dl>

                <GuideVisual guideId={guide.id} />

                {detail?.recommended_setup?.length ? (
                  <section className="rounded-control border border-brand/25 bg-brand-soft p-4">
                    <h3 className="text-sm font-bold text-ink">
                      Что лучше настроить сразу
                    </h3>
                    <ul className="mt-2 grid list-disc gap-2 pl-5 text-sm leading-relaxed text-ink-soft">
                      {detail.recommended_setup.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {detail?.controls?.length ? (
                  <section className="rounded-control border border-line bg-canvas-alt p-4">
                    <h3 className="text-sm font-bold text-ink">
                      Что делает каждая кнопка
                    </h3>
                    <dl className="mt-3 grid gap-2">
                      {detail.controls.map((control) => (
                        <div
                          key={control.label}
                          className="rounded-[12px] border border-line bg-surface p-3"
                        >
                          <dt className="text-sm font-bold text-ink">
                            {control.label}
                          </dt>
                          <dd className="mt-1 text-sm leading-6 text-ink-soft">
                            {control.does}{" "}
                            <strong className="font-semibold text-ink">
                              Когда:
                            </strong>{" "}
                            {control.use_when}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </section>
                ) : null}

                {detail?.steps?.length ? (
                  <section className="rounded-control border border-line bg-canvas-alt p-4">
                    <h3 className="text-sm font-bold text-ink">Что делать</h3>
                    <ol className="mt-2 grid list-decimal gap-2 pl-5 text-sm leading-relaxed text-ink-soft">
                      {detail.steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </section>
                ) : null}

                {detail?.warnings?.length ? (
                  <section className="rounded-control border border-[#f0c36d] bg-[#fff8e8] p-4">
                    <h3 className="text-sm font-bold text-[#6f4d08]">
                      Не делайте так
                    </h3>
                    <ul className="mt-2 grid list-disc gap-2 pl-5 text-sm leading-relaxed text-[#765d2d]">
                      {detail.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {detail?.failure_steps?.length ? (
                  <details className="rounded-control border border-line bg-surface px-4 py-3 text-sm">
                    <summary className="min-h-8 cursor-pointer font-semibold text-ink">
                      Если не получилось
                    </summary>
                    <ul className="mt-2 grid list-disc gap-2 pl-5 leading-relaxed text-ink-soft">
                      {detail.failure_steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ul>
                  </details>
                ) : null}
              </div>
            </details>
          );
        })}
      </div>

      {visible.length === 0 && atlasMatches.length === 0 ? (
        <Card className="text-sm leading-relaxed text-ink-soft">
          Ничего не найдено. Сбросьте категорию или попробуйте название кнопки,
          клиента либо платформы. Если задачи всё равно нет, отправьте её в
          поддержку — запрос попадёт в очередь покрытия справочника.
        </Card>
      ) : null}
    </>
  );
}
