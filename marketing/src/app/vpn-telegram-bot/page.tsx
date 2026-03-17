import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN Telegram bot | PORTAL",
  "VPN Telegram bot для быстрого запуска теста, получения ключа и перехода в WebApp без лишних шагов.",
);

export default function VpnTelegramBotPage() {
  return (
    <MarketingLanding
      heroKicker="SEO landing • VPN Telegram bot"
      heroTitle="VPN Telegram bot для тех, кто хочет сразу зайти в тест, а не в холодную оплату"
      heroSubtitle="PORTAL использует Telegram-бота как главный конверсионный экран: запуск теста, выдача ключа, быстрые инструкции и перевод в WebApp без лишнего шума."
      clusterTitle="Кластер вокруг bot-first сценария"
      clusterBody="Эта посадка усиливает интент по запросам про Telegram-боты и ведёт пользователя в основной путь: бот, тест, апгрейд, продление."
    />
  );
}
