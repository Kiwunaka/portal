import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "TikTok: проверка через приложение | POKROV",
  "Приложение, 5 дней бесплатно и проверка коротких видео без лишней настройки.",
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
          heroTitle="TikTok с быстрым стартом для проверки"
          heroSubtitle="Проверьте TikTok в приложении, а уже потом решите в кабинете, хотите ли продолжать."
          scenarioTitle="Как проверить TikTok без лишнего шума"
          scenarioBody="Когда вы смотрите короткие видео, важны быстрый старт, реальная проверка и минимум действий до первого просмотра."
          scenarioCards={[
            {
              eyebrow: "Мгновенный старт",
              glyph: "arc",
              title: "Проверка начинается почти сразу",
              desc: "Android- или Windows-приложение быстро доводит до реального теста, чтобы вы смотрели видео, а не разбирались в технических деталях.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "route",
              title: "Приложение для опыта, кабинет для решения",
              desc: "Сайт отвечает за вход, приложение — за первый личный тест, кабинет — за управление доступом дальше.",
            },
            {
              eyebrow: "Служба заботы",
              glyph: "shield",
              title: "Поддержка остаётся рядом",
              desc: "Telegram и команда заботы помогают быстро решить вопрос и не перегружают вас лишним шумом.",
            },
          ]}
          clusterTitle="Ещё задачи под видео"
          clusterBody="Изучите соседние страницы под привычные сервисы и форматы просмотра."
        />
      </div>
    </>
  );
}
