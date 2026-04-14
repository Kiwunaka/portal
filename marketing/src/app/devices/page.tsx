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
      <MarketingLanding
        pagePath={MARKETING_CANONICAL_PATHS.devices}
        heroKicker="Для всех основных устройств"
        heroTitle="Android и Windows с одним понятным маршрутом"
        heroSubtitle="Для Android и Windows основной путь уже идёт через приложение, тест, кабинет и продление. Для Apple мы честно держим readiness-статус без ложного обещания доступности."
        scenarioTitle="Как устроен маршрут по устройствам"
        scenarioBody="Страница не смешивает релизные обещания и readiness-статус: для Android и Windows путь публичный, для Apple — аккуратное ожидание и инструкции."
        scenarioCards={[
          {
            eyebrow: "Android + Windows",
            glyph: "window",
            title: "Основной релизный путь уже готов",
            desc: "Именно эти платформы входят в текущий public promise, поэтому старт и тест выстроены вокруг них.",
          },
          {
            eyebrow: "Apple readiness",
            glyph: "orbit",
            title: "Работаем над iPhone и Mac",
            desc: "Если устройство Apple важно уже сейчас, страница честно показывает статус готовности без ложных обещаний.",
          },
          {
            eyebrow: "Один бренд-маршрут",
            glyph: "route",
            title: "Единая логика для всех устройств",
            desc: "Сайт отвечает за старт, приложение — за первый опыт, кабинет — за управление вашим доступом.",
          },
        ]}
        clusterTitle="Страница выбора устройства"
        clusterBody="Эта страница ловит device-intent и помогает быстро перейти к нужному сценарию без дублирования главной."
      />
    </>
  );
}
