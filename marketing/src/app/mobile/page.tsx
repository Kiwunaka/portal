import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Мобильный старт | POKROV",
  "POKROV на Android: 5 дней бесплатно без карты, быстрый старт в приложении и управление в кабинете.",
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
          heroTitle="POKROV на Android: 5 дней без карты"
          heroSubtitle="Установите приложение, активируйте бесплатный период и проверьте привычные сервисы на своем телефоне."
          scenarioTitle="Почему это удобно на телефоне"
          scenarioBody="На телефоне важны быстрый запуск, минимум действий и проверка в привычных приложениях."
          scenarioCards={[
            {
              eyebrow: "Мобильный старт",
              glyph: "arc",
              title: "Один короткий шаг к подключению",
              desc: "Android-приложение доводит до первого подключения без ручной настройки и выбора серверов.",
            },
            {
              eyebrow: "Повседневный ритм",
              glyph: "signal",
              title: "Проверяйте там, где пользуетесь каждый день",
              desc: "Открываете привычные приложения и оцениваете связь на собственном устройстве.",
            },
            {
              eyebrow: "Кабинет позже",
              glyph: "route",
              title: "Кабинет рядом для срока и поддержки",
              desc: "Управление доступом, устройствами и обращениями остается в кабинете после первого старта.",
            },
          ]}
          clusterTitle="Когда нужен быстрый старт на телефоне"
          clusterBody="Эта страница ведёт в приложение, кабинет и оплату без смешивания ролей."
        />
      </div>
    </>
  );
}
