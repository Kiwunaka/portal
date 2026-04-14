import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "TikTok без пауз | POKROV",
  "Приложение, 5 дней теста и спокойный маршрут к стабильной ленте и коротким видео без лишней настройки.",
  {
    path: MARKETING_CANONICAL_PATHS.tiktok,
    keywords: ["tiktok без пауз", "стабильный tiktok", "ускорение tiktok", "pokrov tiktok"],
  },
);

export default function TiktokPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "TikTok", path: MARKETING_CANONICAL_PATHS.tiktok },
        ])}
      />
      <MarketingLanding
        pagePath={MARKETING_CANONICAL_PATHS.tiktok}
        heroKicker="Для TikTok и коротких видео"
        heroTitle="TikTok с мгновенным стартом и ровной подачей"
        heroSubtitle="Эта страница помогает быстро проверить качество сети под TikTok и уже потом в кабинете решить, хотите ли вы продолжать."
        scenarioTitle="Почему TikTok идёт ровно"
        scenarioBody="Когда вы смотрите короткие видео, важны мгновенный старт, стабильная связь и отсутствие лишней настройки."
        scenarioCards={[
          {
            eyebrow: "Мгновенный старт",
            glyph: "arc",
            title: "Проверка начинается сразу после установки",
            desc: "Android- или Windows-приложение быстро доводит до реального теста, чтобы вы смотрели видео, а не разбирались в технике.",
          },
          {
            eyebrow: "Понятный путь",
            glyph: "route",
            title: "Приложение для опыта, кабинет для выбора",
            desc: "Сайт отвечает за вход, приложение — за первый опыт, кабинет — за управление доступом.",
          },
          {
            eyebrow: "Служба заботы",
            glyph: "shield",
            title: "Поддержка всегда рядом",
            desc: "Telegram и команда заботы помогают быстро решить вопрос, не раздувая лишний шум.",
          },
        ]}
        clusterTitle="Ещё сценарии под видео"
        clusterBody="Изучите соседние страницы, чтобы настроить свою сеть под привычный формат просмотра."
      />
    </>
  );
}
