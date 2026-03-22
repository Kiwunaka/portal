import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Быстрый VPN на телефон | POKROV VPN",
  "Быстрый старт для телефона: приложение, 5 дней теста и понятное подключение на Android и iPhone.",
);

export default function FastPhoneVpnPage() {
  return (
    <MarketingLanding
      heroKicker="Быстрый старт для телефона"
      heroTitle="VPN на телефон без долгой настройки"
      heroSubtitle="Если хочется быстро проверить сервис на Android или iPhone, начните с приложения, возьмите тест на 5 дней и подключайтесь в привычном ритме. Telegram останется рядом как запасной путь."
      clusterTitle="Когда нужен VPN на телефоне"
      clusterBody="Эта страница помогает быстро перейти к мобильному сценарию и затем аккуратно ведёт в приложение, тест и кабинет."
    />
  );
}
