import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Быстрый VPN на телефон | POKROV VPN",
  "Быстрый старт для телефона: приложение, 5 дней теста и понятный маршрут на Android без пустых технических переходов.",
  {
    path: "/bystryy-vpn-na-telefon/",
    keywords: ["быстрый vpn на телефон", "vpn на телефон", "впн на телефон", "vpn android"],
  },
);

export default function FastPhoneVpnPage() {
  return (
    <MarketingLanding
      heroKicker="Быстрый старт для телефона"
      heroTitle="VPN на телефон без долгой настройки"
      heroSubtitle="Если нужен быстрый мобильный старт, начните с приложения, включите тест на 5 дней и только потом решайте, хотите ли продлевать доступ."
      clusterTitle="Когда нужен VPN на телефоне"
      clusterBody="Эта страница отвечает на мобильный сценарий и аккуратно ведёт в приложение, кабинет и checkout-маршрут без смешивания смыслов."
    />
  );
}
