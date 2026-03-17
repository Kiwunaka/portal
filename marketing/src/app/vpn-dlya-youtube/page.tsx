import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для YouTube через Telegram | PORTAL",
  "VPN для YouTube с bot-first запуском: тест 3 дня, подключение через Telegram и понятный путь к продлению.",
);

export default function VpnForYoutubePage() {
  return (
    <MarketingLanding
      heroKicker="SEO landing • VPN для YouTube"
      heroTitle="VPN для YouTube, который можно поднять через Telegram за пару минут"
      heroSubtitle="Эта страница собрана под поисковый сценарий, когда человеку нужен VPN для YouTube без длинной настройки. Главный шаг остаётся тем же: перейти в бота, запустить тест и проверить сервис на реальном трафике."
      clusterTitle="Кластер вокруг YouTube-сценария"
      clusterBody="Отсюда пользователь может перейти в смежные поисковые ветки: TikTok, VPN Telegram bot, быстрый VPN на телефон и подключение на разных устройствах."
    />
  );
}
