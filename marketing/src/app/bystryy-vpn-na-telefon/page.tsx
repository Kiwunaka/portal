import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Быстрый VPN на телефон | POKROV VPN",
  "Запуск через Telegram, тест на 5 дней и понятное подключение на Android и iPhone.",
);

export default function FastPhoneVpnPage() {
  return (
    <MarketingLanding
      heroKicker="Быстрый старт для телефона"
      heroTitle="VPN на телефон без долгой настройки"
      heroSubtitle="Если хочется быстро проверить сервис на Android или iPhone, начните с Telegram-бота, возьмите тест на 5 дней и подключайтесь в привычном ритме."
      clusterTitle="Когда нужен VPN на телефоне"
      clusterBody="Эта страница помогает быстро перейти к мобильному сценарию и затем аккуратно ведёт в бота, тест и кабинет."
    />
  );
}
