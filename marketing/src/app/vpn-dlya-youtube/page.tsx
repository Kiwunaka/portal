import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

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
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "VPN для YouTube", path: "/vpn-dlya-youtube/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-dlya-youtube/"
        heroKicker="Для YouTube и длинных видео"
        heroTitle="VPN для YouTube без долгого старта"
        heroSubtitle="Сначала проверьте доступ к YouTube в приложении и только потом переходите к кабинету и продлению, если сервис подошёл."
        scenarioTitle="Что важно в YouTube-сценарии"
        scenarioBody="Здесь пользователю важны длинные сессии, предсказуемость подключения и отсутствие лишних промежуточных шагов перед первым тестом."
        scenarioCards={[
          {
            eyebrow: "Длинные видео",
            glyph: "signal",
            title: "Сразу проверяете тот тип сценария, ради которого пришли",
            desc: "Не обещаем абстрактный “быстрый интернет”, а ведём сразу к реальной проверке YouTube через приложение и live-маршрут.",
          },
          {
            eyebrow: "Приложение сначала",
            glyph: "window",
            title: "Никакого скрытого тех-хоста вместо продукта",
            desc: "Первый шаг остаётся прозрачным: приложение, тест и только потом кабинет, если сервис действительно зашёл.",
          },
          {
            eyebrow: "Продление потом",
            glyph: "route",
            title: "Платная часть начинается только после личного выбора",
            desc: "Так маршрут остаётся спокойным: сначала убеждает опыт использования, потом уже открывается продление.",
          },
        ]}
        clusterTitle="Похожие страницы"
        clusterBody="Отсюда удобно перейти к TikTok, телефону и Telegram-сценарию, не дублируя главную страницу и сохраняя один понятный маршрут."
      />
    </>
  );
}
