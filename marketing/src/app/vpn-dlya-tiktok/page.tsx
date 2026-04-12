import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

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
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "VPN для TikTok", path: "/vpn-dlya-tiktok/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-dlya-tiktok/"
        heroKicker="Для TikTok и коротких видео"
        heroTitle="VPN для TikTok с понятным запуском через приложение"
        heroSubtitle="Эта страница помогает быстро проверить сервис под TikTok и уже потом спокойно перейти к кабинету и продлению, если всё подошло."
        scenarioTitle="Что важно в TikTok-сценарии"
        scenarioBody="Когда запрос приходит под короткие видео, особенно важны мгновенный старт, ясный next step и отсутствие ощущения, что вас ведут через сложную настройку."
        scenarioCards={[
          {
            eyebrow: "Мгновенный старт",
            glyph: "arc",
            title: "Проверка начинается сразу после установки",
            desc: "Android- или Windows-приложение быстро доводит до реального теста, чтобы вы смотрели на результат, а не на технику.",
          },
          {
            eyebrow: "Понятный маршрут",
            glyph: "route",
            title: "Каждый шаг объясняет следующий, а не перегружает интерфейс",
            desc: "Сайт отвечает за вход, приложение — за первый опыт, кабинет — за продление и управление доступом.",
          },
          {
            eyebrow: "Поддержка рядом",
            glyph: "shield",
            title: "Если нужен обходной путь, он уже подготовлен",
            desc: "Telegram и служба заботы остаются под рукой, но не подменяют основной сценарий использования.",
          },
        ]}
        clusterTitle="Ещё варианты под видео"
        clusterBody="Связанная группа страниц усиливает поиск по use-case запросам, но не ломает app-first логику продукта."
      />
    </>
  );
}
