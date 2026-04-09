import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

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
    <MarketingLanding
      heroKicker="Для всех основных устройств"
      heroTitle="VPN на iPhone, Android и Windows с одним понятным маршрутом"
      heroSubtitle="Для Android и Windows основной путь уже идёт через приложение, тест, кабинет и продление. Для Apple мы честно держим readiness-статус без ложного обещания доступности."
      clusterTitle="Страница выбора устройства"
      clusterBody="Эта страница ловит device-intent и помогает быстро перейти к нужному сценарию без дублирования главной."
    />
  );
}
