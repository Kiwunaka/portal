import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Мобильный старт | POKROV",
  "Быстрый старт для телефона: приложение, 5 дней теста и спокойная проверка связи на Android.",
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
          heroTitle="Спокойный старт на телефоне"
          heroSubtitle="Если нужен быстрый мобильный маршрут, начните с приложения, включите тест на 5 дней и оцените связь в привычном ритме."
          scenarioTitle="Почему это удобно на телефоне"
          scenarioBody="В мобильном сценарии особенно важны короткий путь к действию, понятная проверка связи и отсутствие лишней настройки."
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
              desc: "Открываете привычные приложения и сами видите, насколько спокойно всё работает в вашем ритме.",
            },
            {
              eyebrow: "Дальше без шума",
              glyph: "route",
              title: "Кабинет остаётся рядом, когда он нужен",
              desc: "Управление доступом ждёт в кабинете только тогда, когда вы уже поняли, что сервис вам подходит.",
            },
          ]}
          clusterTitle="Когда нужен быстрый старт на телефоне"
          clusterBody="Эта страница отвечает на мобильный сценарий и ведёт в приложение, кабинет и оплату без смешивания ролей."
        />
      </div>
    </>
  );
}
