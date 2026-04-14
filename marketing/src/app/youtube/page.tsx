import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "YouTube без пауз | POKROV",
  "Приложение, 5 дней теста и спокойный маршрут к длинным видео и предсказуемой загрузке без лишних шагов.",
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
    keywords: ["youtube без пауз", "стабильный youtube", "ускорение youtube", "pokrov youtube"],
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
      <MarketingLanding
        pagePath={MARKETING_CANONICAL_PATHS.youtube}
        heroKicker="Для YouTube и длинных видео"
        heroTitle="YouTube без пауз и зависаний"
        heroSubtitle="Сначала проверьте качество видео в приложении и только потом переходите к кабинету и продлению, если сервис подошёл."
        scenarioTitle="Почему YouTube идёт стабильно"
        scenarioBody="Здесь важны стабильные маршруты, предсказуемость подключения и отсутствие лишних шагов перед первым запуском."
        scenarioCards={[
          {
            eyebrow: "Длинные видео",
            glyph: "signal",
            title: "Сразу проверяете тот сценарий, ради которого пришли",
            desc: "Маршрут ведёт к реальной проверке видео, а не к абстрактным обещаниям.",
          },
          {
            eyebrow: "Приложение сначала",
            glyph: "window",
            title: "Никакого шума вместо продукта",
            desc: "Первый шаг прозрачен: приложение, тест и только потом кабинет, если скорость вас устроила.",
          },
          {
            eyebrow: "Продление потом",
            glyph: "route",
            title: "Платная часть только по вашему выбору",
            desc: "Сначала личный опыт использования, потом уже решение в кабинете.",
          },
        ]}
        clusterTitle="Похожие сценарии"
        clusterBody="Отсюда удобно перейти к TikTok, мобильному старту и другим страницам с тем же app-first маршрутом."
      />
    </>
  );
}
