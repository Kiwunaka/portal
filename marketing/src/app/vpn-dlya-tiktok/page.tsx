import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "VPN для TikTok | POKROV VPN",
  "Приложение, 5 дней теста и понятное подключение для TikTok-сценария без лишней технической путаницы.",
  {
    path: "/vpn-dlya-tiktok/",
    keywords: ["vpn для tiktok", "впн для tiktok", "tiktok vpn", "vpn tiktok android"],
  },
);

export default function VpnForTiktokPage() {
  return (
    <MarketingLanding
      heroKicker="Для TikTok и коротких видео"
      heroTitle="VPN для TikTok с понятным запуском через приложение"
      heroSubtitle="Эта страница помогает быстро проверить сервис под TikTok и уже потом спокойно перейти к кабинету и продлению, если всё подошло."
      clusterTitle="Ещё варианты под видео"
      clusterBody="Связанная группа страниц усиливает поиск по use-case запросам, но не ломает app-first логику продукта."
    />
  );
}
