import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN на iPhone, Android и Windows | PORTAL",
  "VPN на iPhone, Android и Windows с единым путём через Telegram, тестом на 3 дня и переходом в WebApp.",
);

export default function MultiDeviceVpnPage() {
  return (
    <MarketingLanding
      heroKicker="SEO landing • VPN на iPhone / Android / Windows"
      heroTitle="VPN на iPhone, Android и Windows с одним понятным маршрутом запуска"
      heroSubtitle="Независимо от устройства пользователь проходит один и тот же сценарий: Telegram-бот, тест 3 дня, подключение приложения, затем тарифы и продление внутри экосистемы PORTAL."
      clusterTitle="Кластер вокруг устройств"
      clusterBody="Эта страница закрывает запросы по устройствам и усиливает WebApp-наратив: кабинету не нужно объяснять продукт заново, он продолжает уже понятную воронку."
    />
  );
}
