import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для TikTok через Telegram | PORTAL",
  "VPN для TikTok с тестом на 3 дня, быстрым запуском через Telegram и простым подключением на телефоне.",
);

export default function VpnForTiktokPage() {
  return (
    <MarketingLanding
      heroKicker="SEO landing • VPN для TikTok"
      heroTitle="VPN для TikTok с тестом на 3 дня и понятным запуском через Telegram"
      heroSubtitle="Посадка под TikTok-интент выводит человека не на сложный checkout, а в сценарий, где можно быстро попробовать сервис, подключить телефон и только потом перейти на тариф."
      clusterTitle="Кластер вокруг TikTok и short-video"
      clusterBody="Страница работает как вход для вертикального контента и коротких видео, а дальше переводит пользователя в общую воронку PORTAL без раздвоения оффера."
    />
  );
}
