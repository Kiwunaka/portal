import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN через Telegram-бота | POKROV VPN",
  "Telegram-бот как главный вход: тест, подсказки, кабинет и переход к продлению без лишних шагов.",
);

export default function VpnTelegramBotPage() {
  return (
    <MarketingLanding
      heroKicker="Для тех, кто любит короткий путь"
      heroTitle="Telegram-бот как главный вход в POKROV VPN"
      heroSubtitle="Бот запускает тест, подсказывает следующий шаг и ведёт в кабинет только тогда, когда это уже действительно нужно."
      clusterTitle="Похожие сценарии"
      clusterBody="Эта страница усиливает запросы про Telegram-бота и ведёт в основной маршрут: бот, тест, подключение и продление."
    />
  );
}
