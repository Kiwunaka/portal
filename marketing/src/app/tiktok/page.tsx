import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "TikTok через приложение | POKROV",
  "POKROV для Android и Windows: 5 дней бесплатно без карты, быстрый старт и проверка TikTok без ручных профилей.",
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
          heroTitle="POKROV для TikTok на Android и Windows"
          heroSubtitle="Получите 5 дней бесплатно без карты, откройте POKROV и проверьте короткие видео без ручной настройки."
          scenarioTitle="Как дойти до первого ролика"
          scenarioBody="Для коротких видео важны быстрый старт, видимая кнопка подключения и минимум действий до проверки."
          scenarioCards={[
            {
              eyebrow: "Быстрый старт",
              glyph: "arc",
              title: "Проверяете TikTok до оплаты",
              desc: "Android- или Windows-приложение доводит до реального теста, а не до списка технических настроек.",
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
              desc: "Telegram и команда поддержки помогают решить вопрос по установке, доступу или продлению.",
            },
          ]}
          clusterTitle="Ещё задачи под видео"
          clusterBody="Изучите соседние страницы под привычные сервисы и форматы просмотра."
        />
      </div>
    </>
  );
}
