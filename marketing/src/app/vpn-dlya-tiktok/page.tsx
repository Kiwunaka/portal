import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для TikTok | POKROV VPN",
  "Приложение, тест на 5 дней и понятное подключение для TikTok-сценария.",
);

export default function VpnForTiktokPage() {
  return (
    <MarketingLanding
      heroKicker="Для TikTok и коротких видео"
      heroTitle="VPN для TikTok с понятным запуском через приложение"
      heroSubtitle="Страница помогает быстро проверить сервис, подключить телефон и уже потом спокойно перейти к тарифу, если всё подошло. Telegram остаётся рядом как помощь и резервный сценарий."
      clusterTitle="Ещё варианты под короткие видео"
      clusterBody="Отсюда удобно перейти к похожим сценариям: YouTube, быстрый VPN на телефон и подключение на разных устройствах без повторного объяснения продукта."
    />
  );
}
