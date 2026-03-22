import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN на iPhone, Android и Windows | POKROV VPN",
  "Приложение как основной старт, тест на 5 дней и понятный маршрут к кабинету на основных устройствах.",
);

export default function MultiDeviceVpnPage() {
  return (
    <MarketingLanding
      heroKicker="Для всех основных устройств"
      heroTitle="VPN на iPhone, Android и Windows с одним понятным маршрутом"
      heroSubtitle="Для Android и Windows основной путь уже ведём через приложение, тест на 5 дней, кабинет и продление. Для Apple сейчас честно держим readiness-статус без лишних обещаний."
      clusterTitle="Страница для выбора устройства"
      clusterBody="Здесь можно быстро перейти к сценарию под смартфон или компьютер и не объяснять продукт заново на каждом шаге."
    />
  );
}
