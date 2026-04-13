import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Оптимизатор для Android и Windows | POKROV Network",
  "Приложение как основной старт, 5 дней тест-драйва и идеальное ускорение на всех ваших устройствах.",
  {
    path: "/vpn-na-iphone-android-windows/",
    keywords: ["ускоритель на windows", "ускоритель на android", "стабильная сеть для пк", "оптимизатор интернета"],
  },
);

export default function MultiDeviceVpnPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV Network", path: "/" },
          { name: "Устройства", path: "/vpn-na-iphone-android-windows/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-na-iphone-android-windows/"
        heroKicker="Для всех основных устройств"
        heroTitle="VPN на iPhone, Android и Windows с одним понятным маршрутом"
        heroSubtitle="Для Android и Windows основной путь уже идёт через приложение, тест, кабинет и продление. Для Apple мы честно держим readiness-статус без ложного обещания доступности."
        scenarioTitle="Как устроен маршрут по устройствам"
        scenarioBody="Страница не смешивает релизные обещания и readiness-статус: для Android и Windows путь публичный, для Apple — аккуратное ожидание и инструкции."
        scenarioCards={[
          {
            eyebrow: "Android + Windows",
            glyph: "window",
            title: "Основной релизный путь уже готов",
            desc: "Именно эти платформы входят в текущий public promise, поэтому старт, тест-драйв и ускорение выстроены вокруг них.",
          },
          {
            eyebrow: "Apple readiness",
            glyph: "orbit",
            title: "Работаем над поддержкой iPhone и Mac",
            desc: "Если устройство Apple важно уже сейчас, страница честно показывает статус готовности без ложных обещаний.",
          },
          {
            eyebrow: "Один бренд-маршрут",
            glyph: "route",
            title: "Единая логика для всех устройств",
            desc: "Сайт отвечает за старт, приложение — за магию скорости, кабинет — за управление вашим доступом.",
          },
        ]}
        clusterTitle="Страница выбора устройства"
        clusterBody="Эта страница ловит device-intent и помогает быстро перейти к нужному сценарию без дублирования главной."
      />
    </>
  );
}
