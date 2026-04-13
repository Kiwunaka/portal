import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Оптимизатор для TikTok | POKROV Network",
  "Приложение, 5 дней тест-драйва и идеальное качество видео для TikTok без пауз и долгого ожидания.",
  {
    path: "/vpn-dlya-tiktok/",
    keywords: ["ускорение tiktok", "стабильный tiktok", "tiktok без пауз", "оптимизатор tiktok"],
  },
);

export default function VpnForTiktokPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV Network", path: "/" },
          { name: "Стабильный TikTok", path: "/vpn-dlya-tiktok/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-dlya-tiktok/"
        heroKicker="Для TikTok и коротких видео"
        heroTitle="Доступ к TikTok с мгновенным запуском"
        heroSubtitle="Эта страница помогает быстро проверить качество сети под TikTok и уже потом в кабинете решить, хотите ли вы продолжать."
        scenarioTitle="Почему TikTok летает"
        scenarioBody="Когда вы смотрите короткие видео, важны мгновенный старт, стабильная связь и отсутствие лишней настройки."
        scenarioCards={[
          {
            eyebrow: "Мгновенный старт",
            glyph: "arc",
            title: "Магия начинается сразу после установки",
            desc: "Android- или Windows-приложение быстро доводит до реального теста, чтобы вы наслаждались видео, а не разбирались в технике.",
          },
          {
            eyebrow: "Понятный путь",
            glyph: "route",
            title: "Никакой путаницы: приложение для опыта, кабинет для выбора",
            desc: "Сайт отвечает за вход, приложение — за первый опыт разгона сети, кабинет — за управление доступом.",
          },
          {
            eyebrow: "Служба экспертов",
            glyph: "shield",
            title: "Забота всегда на связи",
            desc: "Telegram и команда экспертов помогут в любой ситуации, не отрывая вас от любимых видео.",
          },
        ]}
        clusterTitle="Ещё сценарии под видео"
        clusterBody="Изучите соседние страницы, чтобы настроить свою быструю сеть под любой запрос."
      />
    </>
  );
}
