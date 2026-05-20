import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Android и Windows | POKROV",
  "POKROV для Android и Windows: 5 дней бесплатно без карты, до 5 устройств в платных планах и один кабинет.",
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
          heroSubtitle="Текущая бета ведет к приложению, 5 дням бесплатно без карты и кабинету для устройств, продления и поддержки."
          scenarioTitle="Что готово по устройствам"
          scenarioBody="Эта страница показывает текущий пользовательский контур: Android и Windows, один аккаунт, понятное продление."
          scenarioCards={[
            {
              eyebrow: "Android + Windows",
              glyph: "window",
              title: "Бета уже собрана вокруг этих платформ",
              desc: "Android и Windows входят в текущий бета-контур, поэтому старт, бесплатный период и продление выстроены вокруг них.",
            },
            {
              eyebrow: "До 5 устройств",
              glyph: "readiness",
              title: "Платный доступ подходит для нескольких личных устройств",
              desc: "Один аккаунт помогает держать телефон и компьютер рядом: срок, загрузки и поддержка видны в кабинете.",
            },
            {
              eyebrow: "Одна логика",
              glyph: "route",
              title: "Один сценарий для телефона и компьютера",
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
