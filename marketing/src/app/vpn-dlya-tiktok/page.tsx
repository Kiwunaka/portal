import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для TikTok через Telegram | POKROV VPN",
  "Запуск через Telegram, тест на 5 дней и понятное подключение для TikTok-сценария.",
);

export default function VpnForTiktokPage() {
  return (
    <MarketingLanding
      heroKicker="Для TikTok и коротких видео"
      heroTitle="VPN для TikTok с понятным запуском через Telegram"
      heroSubtitle="Страница помогает быстро проверить сервис, подключить телефон и уже потом спокойно перейти к тарифу, если всё подошло."
      clusterTitle="Ещё варианты под короткие видео"
      clusterBody="Отсюда удобно перейти к похожим сценариям: YouTube, быстрый VPN на телефон, Telegram-бот и подключение на разных устройствах."
    />
  );
}
