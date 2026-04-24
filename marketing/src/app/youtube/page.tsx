import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Длинные видео | POKROV",
  "Попробуйте POKROV 5 дней и проверьте длинные ролики, стримы и обучение без лишней настройки.",
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
    keywords: ["длинные видео", "youtube pokrov", "стримы", "видео обучение"],
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
          heroKicker="Длинные видео"
          heroTitle="Длинные ролики, стримы и обучение: сначала проверьте 5 дней"
          heroSubtitle="Сначала проверьте просмотр в приложении 5 дней. Если POKROV подошёл, купите ключ доступа и активируйте его в том же аккаунте."
          scenarioTitle="Что важно для длинных видео"
          scenarioBody="Для длинного просмотра важны ровная загрузка, понятное подключение и отсутствие лишних действий перед первым запуском."
          scenarioCards={[
            {
              eyebrow: "Просмотр",
              glyph: "signal",
              title: "Сразу проверяете нужный формат",
              desc: "Страница ведёт к реальной проверке видео, а не к абстрактным обещаниям.",
            },
            {
              eyebrow: "Приложение сначала",
              glyph: "window",
              title: "Продукт говорит тише рекламы",
              desc: "Первый шаг прозрачен: приложение, 5 дней проверки и только потом кабинет, если качество вас устраивает.",
            },
            {
              eyebrow: "Продление потом",
              glyph: "route",
              title: "Ключ доступа только по вашему решению",
              desc: "Сначала личный опыт, затем спокойное решение о ключе доступа.",
            },
          ]}
          clusterTitle="Похожие задачи"
          clusterBody="Отсюда удобно перейти к коротким видео, мобильному старту и устройствам без повторения одной и той же страницы."
        />
      </div>
    </>
  );
}
