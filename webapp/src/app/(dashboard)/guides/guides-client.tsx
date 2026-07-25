"use client";

import {
  BookOpenCheck,
  CircleCheck,
  Search,
  TriangleAlert,
  X,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  USER_GUIDE_DETAILS,
  USER_GUIDES,
  type UserGuideDetail,
} from "../../../../../shared/trust-and-guides";
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

export function CabinetGuidesClient() {
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

  return (
    <>
      <Link
        href="/guides/pokrov-app/"
        className="flex min-h-24 items-start gap-3 rounded-card border border-brand/30 bg-brand-soft p-4 shadow-soft outline-none hover:border-brand focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-[14px] bg-brand text-white">
          <BookOpenCheck size={22} strokeWidth={2} aria-hidden="true" />
        </span>
        <span>
          <span className="block text-xs font-bold tracking-[0.08em] text-brand uppercase">
            Отдельный атлас Android
          </span>
          <span className="mt-1 block text-base font-bold text-ink">
            Все экраны и кнопки POKROV
          </span>
          <span className="mt-1 block text-sm leading-6 text-ink-muted">
            Реальные скриншоты, точные обводки и рекомендуемый порядок
            настройки.
          </span>
        </span>
      </Link>

      <section className="rounded-card border border-line bg-surface p-4 shadow-soft">
        <label htmlFor="cabinet-guide-search" className="text-sm font-bold text-ink">
          Найти задачу, кнопку или клиент
        </label>
        <div className="relative mt-2">
          <Search
            size={18}
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-muted"
          />
          <input
            id="cabinet-guide-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Happ JSON, WARP, DNS, код или оплата"
            className="min-h-12 w-full rounded-control border border-line bg-canvas py-2 pr-12 pl-10 text-base text-ink outline-none placeholder:text-ink-muted focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Очистить поиск"
              className="absolute top-1/2 right-1.5 grid size-10 -translate-y-1/2 place-items-center rounded-control text-ink-muted outline-none hover:bg-canvas-alt hover:text-ink focus-visible:ring-2 focus-visible:ring-brand"
            >
              <X size={17} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div
          className="mt-4 flex flex-wrap gap-2"
          role="group"
          aria-label="Категория инструкции"
        >
          {categories.map((item) => {
            const selected = category === item.label;
            return (
              <button
                key={item.label}
                type="button"
                aria-pressed={selected}
                onClick={() => setCategory(item.label)}
                className={`min-h-11 rounded-full border px-3.5 py-2 text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 ${
                  selected
                    ? "border-brand bg-brand text-white"
                    : "border-line bg-canvas text-ink-muted hover:border-brand/50 hover:text-ink"
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
      </section>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-ink-muted" aria-live="polite">
          Найдено: <strong className="text-ink">{visible.length}</strong>
        </p>
        {category !== ALL || query ? (
          <button
            type="button"
            onClick={() => {
              setCategory(ALL);
              setQuery("");
            }}
            className="min-h-11 rounded-control px-3 text-sm font-semibold text-brand outline-none hover:bg-brand-soft focus-visible:ring-2 focus-visible:ring-brand"
          >
            Сбросить фильтры
          </button>
        ) : null}
      </div>

      <div className="grid gap-3">
        {visible.map((guide) => {
          const detail = USER_GUIDE_DETAILS[guide.id];
          return (
            <details
              key={guide.id}
              id={guide.id}
              className="group min-w-0 scroll-mt-24 rounded-card border border-line bg-surface p-4 shadow-soft"
            >
              <summary className="min-h-12 cursor-pointer list-none rounded-control outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-bold tracking-[0.08em] text-brand uppercase">
                      {guide.category} · {guide.platform}
                    </p>
                    <p className="mt-1 text-base font-bold text-ink">
                      {guide.title}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-ink-muted">
                      {guide.prerequisites}
                    </p>
                  </div>
                  <Badge tone="neutral">
                    {detail?.steps.length || guide.steps} шаг.
                  </Badge>
                </div>
              </summary>

              <div className="mt-4 border-t border-line pt-4">
                <GuideVisual guideId={guide.id} />

                {detail?.recommended_setup?.length ? (
                  <section className="mt-4 rounded-control border border-brand/25 bg-brand-soft p-3.5">
                    <h3 className="text-sm font-bold text-ink">
                      Настройте сразу
                    </h3>
                    <ul className="mt-2 grid list-disc gap-2 pl-5 text-sm leading-6 text-ink-soft">
                      {detail.recommended_setup.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {detail?.controls?.length ? (
                  <section className="mt-3 rounded-control border border-line bg-canvas-alt p-3.5">
                    <h3 className="text-sm font-bold text-ink">
                      Что делает каждая кнопка
                    </h3>
                    <dl className="mt-2 grid gap-2">
                      {detail.controls.map((control) => (
                        <div
                          key={control.label}
                          className="rounded-control border border-line bg-surface p-3"
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

                <section className="mt-3 rounded-control border border-line bg-canvas-alt p-3.5">
                  <h3 className="text-sm font-bold text-ink">Шаги</h3>
                  <ol className="mt-2 grid list-decimal gap-2 pl-5 text-sm leading-6 text-ink-soft">
                    {(detail?.steps || []).map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>

                {detail?.warnings?.length ? (
                  <section className="mt-3 rounded-control border border-warn-line bg-warn-bg p-3.5 text-warn-text">
                    <h3 className="text-sm font-bold">Не делайте так</h3>
                    <ul className="mt-2 grid list-disc gap-2 pl-5 text-sm leading-6">
                      {detail.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                <div className="mt-3 flex items-start gap-2 rounded-control border border-ok-line bg-ok-bg p-3 text-sm leading-5 text-ok-text">
                  <CircleCheck
                    size={17}
                    strokeWidth={2}
                    aria-hidden="true"
                    className="mt-0.5 shrink-0"
                  />
                  <span>
                    <strong>Результат:</strong> {guide.expected}
                  </span>
                </div>
                <div className="mt-2 flex items-start gap-2 rounded-control border border-warn-line bg-warn-bg p-3 text-sm leading-5 text-warn-text">
                  <TriangleAlert
                    size={17}
                    strokeWidth={2}
                    aria-hidden="true"
                    className="mt-0.5 shrink-0"
                  />
                  <div>
                    <strong>Если не получилось:</strong>
                    <ul className="mt-1 list-disc pl-4">
                      {(detail?.failure_steps || [guide.failure]).map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </details>
          );
        })}
      </div>

      {visible.length === 0 ? (
        <p className="rounded-card border border-line bg-surface p-4 text-sm leading-6 text-ink-muted shadow-soft">
          Ничего не найдено. Сбросьте категорию или ищите по названию кнопки,
          платформы либо клиента.
        </p>
      ) : null}
    </>
  );
}
