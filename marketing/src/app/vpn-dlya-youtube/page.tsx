import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для YouTube | POKROV VPN",
  "Приложение, 5 дней теста и спокойная проверка YouTube-сценария перед выбором тарифа.",
  {
    path: "/vpn-dlya-youtube/",
    keywords: ["vpn для youtube", "впн для youtube", "youtube vpn", "vpn youtube android"],
  },
);

export default function VpnForYoutubePage() {
  return (
    <MarketingLanding
      heroKicker="Для YouTube и длинных видео"
      heroTitle="VPN для YouTube без долгого старта"
      heroSubtitle="Сначала проверьте доступ к YouTube в приложении и только потом переходите к кабинету и продлению, если сервис подошёл."
      clusterTitle="Похожие страницы"
      clusterBody="Отсюда удобно перейти к TikTok, телефону и Telegram-сценарию, не дублируя главную страницу и сохраняя один понятный маршрут."
    />
  );
}
