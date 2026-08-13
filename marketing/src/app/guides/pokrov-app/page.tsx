import JsonLd from "../../../components/json-ld";
import { PageShell } from "../../../components/layout/page-shell";
import {
  buildBreadcrumbJsonLd,
  buildMarketingMetadata,
  MARKETING_CANONICAL_PATHS,
} from "../../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../../lib/pokrov";
import {
  POKROV_ATLAS_CAPTURE,
  POKROV_SCREEN_ATLAS,
} from "../../../../../shared/pokrov-screen-atlas";
import { PokrovAtlasClient } from "./atlas-client";

export const metadata = buildMarketingMetadata(
  "Все экраны приложения POKROV | Подробная инструкция",
  "Полный атлас POKROV для Android: реальные снимки экранов, точные обводки кнопок, объяснения, рекомендуемые настройки и восстановление.",
  { path: MARKETING_CANONICAL_PATHS.guidesPokrovApp },
);

export default function PokrovAppGuidePage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Инструкции", path: MARKETING_CANONICAL_PATHS.guides },
          {
            name: "Все экраны POKROV",
            path: MARKETING_CANONICAL_PATHS.guidesPokrovApp,
          },
        ])}
      />

      <section className="mx-auto flex max-w-6xl flex-col gap-4 px-4 pt-10 pb-8 sm:px-6 sm:pt-14">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          {POKROV_SCREEN_ATLAS.length} экранов · поиск по кнопкам
        </span>
        <h1 className="max-w-4xl font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          Найдите нужный экран POKROV
        </h1>
        <p className="max-w-2xl text-base leading-7 text-ink-soft">
          Ищите по названию кнопки или настройке. Все экраны сначала свёрнуты:
          откройте один и получите снимок, назначение кнопок и безопасные шаги.
        </p>
        <details className="max-w-4xl rounded-control border border-line bg-canvas-alt px-4 py-3 text-sm text-ink-soft">
          <summary className="min-h-8 cursor-pointer font-semibold text-ink">
            Как читать атлас и откуда снимки
          </summary>
          <div className="mt-2 grid gap-2 leading-6">
            <p>
              Красная рамка показывает точную зону нажатия; номер и объяснение
              вынесены под снимок и ничего не закрывают.
            </p>
            <p>
              Снимки: Android {POKROV_ATLAS_CAPTURE.appVersion},{" "}
              {POKROV_ATLAS_CAPTURE.environment}, дата {POKROV_ATLAS_CAPTURE.date}.{" "}
              {POKROV_ATLAS_CAPTURE.privacy}
            </p>
          </div>
        </details>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <PokrovAtlasClient />
      </section>
    </PageShell>
  );
}
