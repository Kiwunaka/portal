import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Мобильный старт | POKROV",
  "Быстрый старт для телефона: приложение POKROV, 5 дней бесплатно и проверка на Android.",
  {
    path: MARKETING_CANONICAL_PATHS.mobile,
    keywords: ["проверка связи на телефон", "android", "мобильный старт", "pokrov на телефон"],
  },
);

export default function MobilePage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "Мобильный старт", path: MARKETING_CANONICAL_PATHS.mobile },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--mobile">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.mobile}
          heroKicker="Мобильный старт"
          heroTitle="POKROV на телефоне за один старт"
          heroSubtitle="Установите приложение, включите 5 дней бесплатно и проверьте POKROV в своих сервисах."
          scenarioTitle="Почему это удобно на телефоне"
          scenarioBody="На телефоне важны быстрый запуск, минимум действий и проверка в привычных приложениях."
          scenarioCards={[
            {
              eyebrow: "Мобильный старт",
              glyph: "arc",
              title: "Один короткий шаг к проверке",
              desc: "Android-приложение быстро доводит до реального опыта без прыжков по техническим ссылкам и без сложного старта.",
            },
            {
              eyebrow: "Повседневный ритм",
              glyph: "signal",
              title: "Проверяете связь там, где живёте каждый день",
              desc: "Открываете привычные приложения и сами решаете, подходит ли POKROV для ежедневного использования.",
            },
            {
              eyebrow: "Кабинет позже",
              glyph: "route",
              title: "Кабинет остаётся рядом, когда он нужен",
              desc: "Управление доступом ждёт в кабинете только тогда, когда вы уже поняли, что сервис вам подходит.",
            },
          ]}
          clusterTitle="Когда нужен быстрый старт на телефоне"
          clusterBody="Эта страница ведёт в приложение, кабинет и оплату без смешивания ролей."
        />
      </div>
    </>
  );
}
