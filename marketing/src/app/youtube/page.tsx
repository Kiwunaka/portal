import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "YouTube: спокойная проверка | POKROV",
  "Приложение, 5 дней теста и спокойный маршрут для проверки длинных видео без лишних шагов.",
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
    keywords: ["проверка youtube", "длинные видео", "pokrov youtube", "маршрут для видео"],
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
          heroTitle="YouTube без лишних шагов до проверки"
          heroSubtitle="Сначала спокойно проверьте качество видео в приложении и только потом переходите к кабинету и продлению, если сервис действительно подошёл."
          scenarioTitle="Как проверить YouTube в понятном маршруте"
          scenarioBody="Здесь особенно важны устойчивый маршрут, предсказуемый первый запуск и отсутствие лишних шагов перед проверкой."
          scenarioCards={[
            {
              eyebrow: "Длинные видео",
              glyph: "signal",
              title: "Сразу проверяете нужный сценарий",
              desc: "Маршрут ведёт к реальной проверке видео, а не к абстрактным обещаниям или декоративной витрине.",
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
              desc: "Сначала личный опыт использования, затем уже спокойное решение о продлении в кабинете.",
            },
          ]}
          clusterTitle="Похожие сценарии"
          clusterBody="Отсюда удобно перейти к TikTok, мобильному старту и другим страницам с тем же понятным маршрутом и более спокойным тоном."
        />
      </div>
    </>
  );
}
