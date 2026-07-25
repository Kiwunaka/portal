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

      <section className="mx-auto flex max-w-6xl flex-col gap-4 px-4 pt-12 pb-8 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          {POKROV_SCREEN_ATLAS.length} экранов и панелей · Android{" "}
          {POKROV_ATLAS_CAPTURE.appVersion} · снято{" "}
          {POKROV_ATLAS_CAPTURE.date}
        </span>
        <h1 className="max-w-4xl font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          Весь POKROV по экранам и кнопкам
        </h1>
        <p className="max-w-4xl text-base leading-7 text-ink-soft">
          Это отдельная подробная инструкция по текущей Android-бете. На каждом
          реальном снимке красной рамкой отмечена точная зона; текст и номер
          вынесены под изображение и ничего не закрывают. Для каждой кнопки
          указано, что она делает, когда её нажимать и что лучше настроить сразу.
        </p>
        <p className="max-w-4xl rounded-control border border-line bg-canvas-alt p-3.5 text-sm leading-6 text-ink-soft">
          Снимки: {POKROV_ATLAS_CAPTURE.environment}.{" "}
          {POKROV_ATLAS_CAPTURE.privacy} Системные страницы Android, кабинет и
          платёжный провайдер показаны как переходы: это отдельные интерфейсы,
          которыми POKROV не должен притворяться.
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <PokrovAtlasClient />
      </section>
    </PageShell>
  );
}
