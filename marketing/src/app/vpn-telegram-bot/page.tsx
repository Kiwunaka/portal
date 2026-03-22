import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Telegram и поддержка | POKROV VPN",
  "Telegram как запасной путь, поддержка и продолжение сценария после входа в приложение или кабинет.",
);

export default function VpnTelegramBotPage() {
  return (
    <MarketingLanding
      heroKicker="Для тех, кто любит короткий путь"
      heroTitle="Telegram как быстрый резервный маршрут POKROV VPN"
      heroSubtitle="Бот помогает продолжить сценарий, если нужен быстрый вход, персональная ссылка на оплату, поддержка или восстановление доступа. Но основной путь релиза мы строим через приложение."
      clusterTitle="Похожие сценарии"
      clusterBody="Эта страница усиливает запросы про Telegram и всё равно аккуратно ведёт в основной маршрут: приложение, тест, кабинет и продление."
    />
  );
}
