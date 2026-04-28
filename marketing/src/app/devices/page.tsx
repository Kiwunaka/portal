import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Android и Windows | POKROV",
  "Приложение как основной старт, 5 дней теста и понятный маршрут по устройствам без ложных обещаний.",
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
          heroTitle="Android и Windows без лишней суеты"
          heroSubtitle="Для Android и Windows путь уже выстроен вокруг приложения, пробного периода и кабинета. Для Apple мы сохраняем спокойный readiness-статус без обещаний раньше времени."
          scenarioTitle="Как устроен маршрут по устройствам"
          scenarioBody="Эта страница помогает быстро понять, где путь уже готов, а где пока стоит честное ожидание без рекламного шума."
          scenarioCards={[
            {
              eyebrow: "Android + Windows",
              glyph: "window",
              title: "Бета-путь уже собран",
              desc: "Именно эти платформы входят в текущий бета-контур, поэтому старт, тест и продление выстроены вокруг них.",
            },
            {
              eyebrow: "Apple readiness",
              glyph: "readiness",
              title: "iPhone и Mac остаются в спокойной готовности",
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
          clusterBody="Страница ловит device-intent и мягко переводит в нужный сценарий, не дублируя главную и не создавая лишний шум."
        />
      </div>
    </>
  );
}
