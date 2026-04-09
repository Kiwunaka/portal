import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Telegram и служба заботы | POKROV VPN",
  "Telegram как запасной путь, служба заботы и продолжение сценария после входа в приложение или кабинет.",
  {
    path: "/vpn-telegram-bot/",
    keywords: ["vpn telegram bot", "telegram vpn bot", "vpn telegram", "pokrov telegram bot"],
  },
);

export default function VpnTelegramBotPage() {
  return (
    <MarketingLanding
      heroKicker="Telegram как продолжение, а не замена"
      heroTitle="Telegram как быстрый резервный маршрут POKROV VPN"
      heroSubtitle="Бот помогает продолжить сценарий, если нужен личный checkout-маршрут, поддержка или восстановление доступа. Но основной публичный вход в продукт остаётся через приложение."
      clusterTitle="Похожие сценарии"
      clusterBody="Страница усиливает Telegram-запросы и при этом аккуратно возвращает пользователя к app-first логике релиза."
    />
  );
}
