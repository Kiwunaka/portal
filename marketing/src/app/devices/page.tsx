import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Android и Windows | POKROV",
  "POKROV для Android и Windows: 5 дней доступа без карты, до 5 устройств в платных планах и честный статус Apple.",
  {
    path: MARKETING_CANONICAL_PATHS.devices,
    keywords: ["android и windows", "устройства pokrov", "оптимизация на пк", "мобильный и десктопный старт"],
  },
);

export default function DevicesPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "Устройства", path: MARKETING_CANONICAL_PATHS.devices },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--devices">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.devices}
          heroKicker="Для основных устройств"
          heroTitle="Android и Windows в одном аккаунте POKROV"
          heroSubtitle="Текущая бета ведет к приложению, 5 дням доступа без карты и кабинету. Apple остается в подготовке без обещаний раньше времени."
          scenarioTitle="Что готово по устройствам"
          scenarioBody="Эта страница сразу показывает, где старт уже готов, а где пока стоит честное ожидание без рекламного шума."
          scenarioCards={[
            {
              eyebrow: "Android + Windows",
              glyph: "window",
              title: "Бета уже собрана вокруг этих платформ",
              desc: "Android и Windows входят в текущий бета-контур, поэтому старт, бесплатный период и продление выстроены вокруг них.",
            },
            {
              eyebrow: "Apple readiness",
              glyph: "readiness",
              title: "iPhone и Mac остаются в подготовке",
              desc: "Если вам важно устройство Apple, страница честно показывает статус и не обещает больше, чем уже готово.",
            },
            {
              eyebrow: "Одна логика",
              glyph: "route",
              title: "Один тон для всех устройств",
              desc: "Сайт помогает начать, приложение даёт первый опыт, а кабинет берёт на себя управление доступом дальше.",
            },
          ]}
          clusterTitle="Выбор устройства без перегруза"
          clusterBody="Страница отвечает на вопрос по устройствам и ведёт к приложению, кабинету или поддержке."
        />
      </div>
    </>
  );
}
