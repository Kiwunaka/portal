import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "TikTok через приложение | POKROV",
  "POKROV для Android и Windows: 5 дней доступа без карты, быстрый старт и короткие видео без ручных профилей.",
  {
    path: MARKETING_CANONICAL_PATHS.tiktok,
    keywords: ["проверка tiktok", "короткие видео", "pokrov tiktok", "мобильный старт"],
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
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--tiktok">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.tiktok}
          heroKicker="Для TikTok и коротких видео"
          heroTitle="TikTok с быстрым стартом в приложении"
          heroSubtitle="Получите 5 дней доступа без карты, откройте POKROV и смотрите короткие видео без ручной настройки."
          scenarioTitle="Как дойти до первого просмотра"
          scenarioBody="Когда вы смотрите короткие видео, важны быстрый старт, видимая кнопка подключения и минимум действий до первого просмотра."
          scenarioCards={[
            {
              eyebrow: "Мгновенный старт",
              glyph: "arc",
              title: "Первый просмотр начинается быстрее",
              desc: "Android- или Windows-приложение быстро доводит до реального теста, чтобы вы смотрели видео, а не разбирались в технических деталях.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "route",
              title: "Приложение для опыта, кабинет для решения",
              desc: "Сайт отвечает за вход, приложение — за первый личный тест, кабинет — за управление доступом дальше.",
            },
            {
              eyebrow: "Поддержка",
              glyph: "shield",
              title: "Поддержка остается рядом",
              desc: "Telegram и команда поддержки помогают быстро решить вопрос по установке, доступу или продлению.",
            },
          ]}
          clusterTitle="Ещё задачи под видео"
          clusterBody="Изучите соседние страницы под привычные сервисы и форматы просмотра."
        />
      </div>
    </>
  );
}
