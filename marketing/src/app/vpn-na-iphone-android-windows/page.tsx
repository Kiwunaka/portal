import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN на iPhone, Android и Windows | POKROV VPN",
  "Telegram как единый старт, тест на 5 дней и понятный маршрут к кабинету на основных устройствах.",
);

export default function MultiDeviceVpnPage() {
  return (
    <MarketingLanding
      heroKicker="Для всех основных устройств"
      heroTitle="VPN на iPhone, Android и Windows с одним понятным маршрутом"
      heroSubtitle="Независимо от устройства путь остаётся одинаковым: Telegram-бот, тест на 5 дней, кабинет и продление, если сервис вам подходит."
      clusterTitle="Страница для выбора устройства"
      clusterBody="Здесь можно быстро перейти к сценарию под смартфон или компьютер и не объяснять продукт заново на каждом шаге."
    />
  );
}
