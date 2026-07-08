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
      heroKicker="Для YouTube и длинных видео"
      heroTitle="Проверьте YouTube через POKROV"
      heroSubtitle="Скачайте приложение, нажмите «Подключить» и откройте свои обычные видео. Проверка бесплатна: 5 дней без карты."
      scenarioTitle="Как дойти до первого видео"
      scenarioBody="Без ручных профилей: ставите приложение, включаете подключение и смотрите результат на своей сети."
      scenarioCards={[
        {
          eyebrow: "Сначала проверка",
          title: "YouTube — до оплаты",
          desc: "Первые 5 дней бесплатны. Откройте своё обычное видео и посмотрите на качество сами.",
        },
        {
          eyebrow: "Одна кнопка",
          title: "Без ручных настроек",
          desc: "Не нужно выбирать сервер и разбираться в протоколах — приложение уже настроено.",
        },
        {
          eyebrow: "Всё остальное — тоже",
          title: "Российские сайты не ломаются",
          desc: "Маршрут «всё, кроме РУ»: банк и госуслуги продолжают открываться напрямую.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
