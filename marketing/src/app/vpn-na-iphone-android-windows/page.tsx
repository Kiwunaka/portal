import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "VPN на iPhone, Android и Windows | POKROV VPN",
  "Приложение как основной старт, тест на 5 дней и понятный маршрут к кабинету на основных устройствах.",
  {
    path: "/vpn-na-iphone-android-windows/",
    keywords: ["vpn на iphone android windows", "впн iphone android windows", "vpn для windows", "vpn для android"],
  },
);

export default function MultiDeviceVpnPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "VPN на iPhone, Android и Windows", path: "/vpn-na-iphone-android-windows/" },
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
            desc: "Именно эти платформы входят в текущий public promise, поэтому старт, тест и продление выстроены вокруг них.",
          },
          {
            eyebrow: "Apple readiness",
            glyph: "orbit",
            title: "Никаких ложных обещаний по iPhone и Mac",
            desc: "Если устройство Apple важно уже сейчас, страница честно показывает readiness-направление без подмены обещаний.",
          },
          {
            eyebrow: "Один бренд-маршрут",
            glyph: "route",
            title: "Какое бы устройство вы ни искали, логика остаётся одной",
            desc: "Сайт отвечает за вход и выбор, приложение — за первый опыт, кабинет — за продолжение и управление доступом.",
          },
        ]}
        clusterTitle="Страница выбора устройства"
        clusterBody="Эта страница ловит device-intent и помогает быстро перейти к нужному сценарию без дублирования главной."
      />
    </>
  );
}
