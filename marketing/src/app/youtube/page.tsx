import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "YouTube через приложение | POKROV",
  "POKROV для Android и Windows: 5 дней бесплатно без карты, быстрый старт и проверка YouTube без сложной настройки.",
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
    keywords: ["проверка youtube", "длинные видео", "pokrov youtube", "видео через pokrov"],
  },
);

export default function YoutubePage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "YouTube", path: MARKETING_CANONICAL_PATHS.youtube },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--youtube">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.youtube}
          heroKicker="Для YouTube и длинных видео"
          heroTitle="POKROV для YouTube на Android и Windows"
          heroSubtitle="Скачайте POKROV, получите 5 дней бесплатно без карты и проверьте длинные видео на своем устройстве."
          scenarioTitle="Как дойти до первого видео"
          scenarioBody="Здесь важны быстрый запуск, понятная кнопка подключения и реальная проверка на вашем устройстве."
          scenarioCards={[
            {
              eyebrow: "Длинные видео",
              glyph: "signal",
              title: "Проверяете YouTube до оплаты",
              desc: "Сначала приложение и 5 дней бесплатно. Если качество устраивает, продлеваете срок в кабинете.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "window",
              title: "Одна кнопка вместо настроек",
              desc: "Не нужно выбирать сервер и настраивать что-то вручную. POKROV всё сделает сам.",
            },
            {
              eyebrow: "Продление потом",
              glyph: "route",
              title: "Платная часть только после теста",
              desc: "Сначала личный опыт использования, затем решение о продлении в кабинете.",
            },
          ]}
          clusterTitle="Похожие задачи"
          clusterBody="Отсюда удобно перейти к TikTok, мобильному старту и другим страницам под привычные сервисы."
        />
      </div>
    </>
  );
}
