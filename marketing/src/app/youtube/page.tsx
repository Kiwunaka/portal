import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "YouTube через приложение | POKROV",
  "POKROV для Android и Windows: 5 дней доступа без карты, быстрый старт и просмотр длинных видео без ручных профилей.",
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
          heroTitle="YouTube на ваших устройствах без ручных профилей"
          heroSubtitle="Скачайте POKROV, получите 5 дней доступа без карты и смотрите видео в приложении на Android или Windows."
          scenarioTitle="Как начать смотреть быстрее"
          scenarioBody="Здесь важны быстрый запуск, предсказуемый первый экран и реальный опыт на видео, а не обещания в вакууме."
          scenarioCards={[
            {
              eyebrow: "Длинные видео",
              glyph: "signal",
              title: "Сразу открываете нужное видео",
              desc: "Страница ведет к приложению и первому просмотру, а не к абстрактным обещаниям.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "window",
              title: "Меньше рекламы, больше конкретики",
              desc: "Первый шаг прозрачен: приложение, бесплатный период и кабинет для продления, если качество связи устраивает.",
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
