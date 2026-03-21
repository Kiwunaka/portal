import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для YouTube через Telegram | POKROV VPN",
  "Запуск через Telegram, тест на 5 дней и спокойная проверка YouTube-сценария перед выбором тарифа.",
);

export default function VpnForYoutubePage() {
  return (
    <MarketingLanding
      heroKicker="Для YouTube и длинных видео"
      heroTitle="VPN для YouTube без долгого старта"
      heroSubtitle="Если хочется просто проверить доступ к YouTube и не возиться с длинной настройкой, начните с Telegram-бота и протестируйте сервис в своём темпе."
      clusterTitle="Похожие страницы"
      clusterBody="Отсюда удобно перейти к TikTok, Telegram-боту, телефону и другим сценариям, где нужен тот же короткий и понятный маршрут."
    />
  );
}
