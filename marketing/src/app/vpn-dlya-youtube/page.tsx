import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для YouTube | POKROV VPN",
  "Приложение, тест на 5 дней и спокойная проверка YouTube-сценария перед выбором тарифа.",
);

export default function VpnForYoutubePage() {
  return (
    <MarketingLanding
      heroKicker="Для YouTube и длинных видео"
      heroTitle="VPN для YouTube без долгого старта"
      heroSubtitle="Если хочется просто проверить доступ к YouTube и не возиться с длинной настройкой, начните с приложения и протестируйте сервис в своём темпе. Telegram остаётся рядом как запасной путь."
      clusterTitle="Похожие страницы"
      clusterBody="Отсюда удобно перейти к TikTok, телефону и другим сценариям, где нужен тот же короткий и понятный маршрут."
    />
  );
}
