import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Короткие видео | POKROV",
  "Попробуйте POKROV 5 дней и проверьте короткие видео, ленту и сторис без лишней настройки.",
  {
    path: MARKETING_CANONICAL_PATHS.tiktok,
    keywords: ["короткие видео", "tiktok pokrov", "лента видео", "сторис"],
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
          heroKicker="Короткие видео"
          heroTitle="Лента, сторис и короткие ролики: проверьте POKROV 5 дней"
          heroSubtitle="Начните с приложения, нажмите «Попробовать 5 дней» и проверьте короткие видео в своём обычном ритме. Если подходит, продолжайте через ключ доступа."
          scenarioTitle="Что важно для коротких видео"
          scenarioBody="Короткие ролики не терпят долгого старта. Поэтому путь ведёт к приложению, быстрой проверке и понятному продлению, если всё подошло."
          scenarioCards={[
            {
              eyebrow: "Быстрый старт",
              glyph: "arc",
              title: "Проверка начинается почти сразу",
              desc: "Android- или Windows-приложение быстро доводит до проверки, чтобы вы смотрели видео, а не разбирались в настройках.",
            },
            {
              eyebrow: "Понятный путь",
              glyph: "route",
              title: "Приложение для опыта, кабинет для решения",
              desc: "Сайт ведёт к старту, приложение даёт первый опыт, кабинет помогает купить и активировать ключ доступа дальше.",
            },
            {
              eyebrow: "Поддержка",
              glyph: "shield",
              title: "Поддержка остаётся рядом",
              desc: "Telegram и команда заботы помогают быстро решить вопрос и не перегружают вас лишним шумом.",
            },
          ]}
          clusterTitle="Ещё страницы под просмотр"
          clusterBody="Для длинных роликов есть отдельная страница, а для установки и устройств — свои короткие объяснения."
        />
      </div>
    </>
  );
}
