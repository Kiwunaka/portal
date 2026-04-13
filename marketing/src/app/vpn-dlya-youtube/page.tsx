import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Оптимизация YouTube | POKROV Network",
  "Приложение, 5 дней тест-драйва и идеальная работа YouTube-сценария без пауз и долгого ожидания.",
  {
    path: "/vpn-dlya-youtube/",
    keywords: ["ускорение youtube", "стабильный youtube", "youtube без пауз", "оптимизатор youtube"],
  },
);

export default function VpnForYoutubePage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV Network", path: "/" },
          { name: "Ускорение YouTube", path: "/vpn-dlya-youtube/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-dlya-youtube/"
        heroKicker="Для YouTube и длинных видео"
        heroTitle="Доступ к YouTube без пауз и зависаний"
        heroSubtitle="Сначала проверьте качество видео в приложении и только потом переходите к кабинету и продлению, если сервис подошёл."
        scenarioTitle="Почему YouTube летает"
        scenarioBody="Здесь важны стабильные маршруты, предсказуемость подключения и отсутствие лишних шагов перед первым запуском."
        scenarioCards={[
          {
            eyebrow: "Длинные видео",
            glyph: "signal",
            title: "Сразу проверяете тот сценарий, ради которого пришли",
            desc: "Не обещаем абстракций, а ведём сразу к реальной проверке видео 4K через приложение и live-маршрут.",
          },
          {
            eyebrow: "Приложение сначала",
            glyph: "window",
            title: "Никакого шума вместо продукта",
            desc: "Первый шаг прозрачен: приложение, тест и только потом кабинет, если скорость вас устроила.",
          },
          {
            eyebrow: "Продление потом",
            glyph: "route",
            title: "Платная часть только по вашему выбору",
            desc: "Маршрут остаётся спокойным: сначала личный опыт использования, потом уже решение в кабинете.",
          },
        ]}
        clusterTitle="Похожие сценарии"
        clusterBody="Отсюда удобно перейти к TikTok, играм и другим страницам, сохраняя один понятный путь к быстрой сети."
      />
    </>
  );
}
