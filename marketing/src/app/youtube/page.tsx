import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "YouTube: проверка через приложение | POKROV",
  "Приложение, 5 дней бесплатно и проверка длинных видео без ручных настроек.",
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
          heroTitle="YouTube: проверьте на своих устройствах"
          heroSubtitle="Сначала проверьте качество видео в приложении. Если POKROV подошёл, продлите доступ в кабинете."
          scenarioTitle="Как проверить YouTube без лишней настройки"
          scenarioBody="Здесь важны быстрый запуск, предсказуемый первый экран и проверка на реальном видео."
          scenarioCards={[
            {
              eyebrow: "Длинные видео",
              glyph: "signal",
              title: "Сразу проверяете нужное видео",
              desc: "Страница ведёт к реальной проверке, а не к абстрактным обещаниям.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "window",
              title: "Продукт говорит тише рекламы",
              desc: "Первый шаг прозрачен: приложение, тест и только потом кабинет, если качество связи вас устраивает.",
            },
            {
              eyebrow: "Продление потом",
              glyph: "route",
              title: "Платная часть только по вашему решению",
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
