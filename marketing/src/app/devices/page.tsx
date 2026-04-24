import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Android и Windows | POKROV без возни",
  "Где POKROV уже доступен публично: Android и Windows, 5 дней проверки, кабинет и честный статус Apple.",
  {
    path: MARKETING_CANONICAL_PATHS.devices,
    keywords: ["android и windows", "устройства pokrov", "приложение для компьютера", "мобильный и настольный старт"],
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
          heroTitle="Android и Windows уже в публичном пути"
          heroSubtitle="На этих устройствах можно установить приложение, нажать «Попробовать 5 дней» и дальше продлить доступ через ключ. Apple честно остаётся в подготовке."
          scenarioTitle="Как выбрать устройство"
          scenarioBody="Эта страница помогает быстро понять, где POKROV уже готов для публичного старта, а где пока стоит честное ожидание без рекламного шума."
          scenarioCards={[
            {
              eyebrow: "Android + Windows",
              glyph: "window",
              title: "Старт уже собран",
              desc: "Именно эти платформы входят в текущий публичный запуск, поэтому установка, проверка и продление выстроены вокруг них.",
            },
            {
              eyebrow: "Apple готовится",
              glyph: "orbit",
              title: "iPhone и Mac пока готовятся",
              desc: "Если вам важно устройство Apple, страница честно показывает статус и не обещает больше, чем уже готово.",
            },
            {
              eyebrow: "Одна логика",
              glyph: "route",
              title: "Одна логика для всех устройств",
              desc: "Сайт помогает начать, приложение даёт первый опыт, а кабинет берёт на себя управление доступом дальше.",
            },
          ]}
          clusterTitle="Выбор устройства без перегруза"
          clusterBody="Страница помогает выбрать устройство и мягко ведёт к установке, не дублируя главную и не создавая лишний шум."
        />
      </div>
    </>
  );
}
