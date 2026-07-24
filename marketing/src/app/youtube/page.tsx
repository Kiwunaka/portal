import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getSeoPage } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.youtube);

export const metadata = buildMarketingMetadata(
  seoPage.title,
  seoPage.description,
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
  },
);

export default function YoutubePage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.youtube}
      breadcrumbName="YouTube"
      heroKicker="Лучший VPN для YouTube · 5 дней за 0 ₽"
      heroTitle="Смотрите YouTube в нужном качестве — без ручной настройки VPN"
      heroSubtitle="Скачайте POKROV, нажмите «Подключить» и проверьте ролики, стримы и перемотку на своей сети. 5 дней бесплатно, карта не нужна."
      scenarioTitle="От установки до первого видео — три шага"
      scenarioBody="POKROV уже настроен: скачайте, подключитесь и оцените результат до оплаты."
      scenarioCards={[
        {
          eyebrow: "5 дней бесплатно",
          title: "Проверьте YouTube до оплаты",
          desc: "Откройте обычные ролики, длинные видео и стримы в нужном качестве на Wi-Fi и мобильной сети.",
        },
        {
          eyebrow: "Одна кнопка",
          title: "Без профилей и протоколов",
          desc: "Не нужно копировать ключи и часами выбирать сервер — приложение делает стартовую настройку за вас.",
        },
        {
          eyebrow: "Умный маршрут",
          title: "Российские сайты идут напрямую",
          desc: "В режиме «всё, кроме РУ» банки, госуслуги и другие российские сайты не отправляются в туннель.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
