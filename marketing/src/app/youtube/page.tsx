import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "YouTube без замедлений | POKROV для Android и Windows",
  "POKROV возвращает YouTube нормальную скорость: 5 дней бесплатно без карты, одна кнопка в приложении, полное качество видео.",
  {
    path: MARKETING_CANONICAL_PATHS.youtube,
    keywords: ["проверка youtube", "youtube замедление", "длинные видео", "pokrov youtube", "видео через pokrov"],
  },
);

export default function YoutubePage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.youtube}
      breadcrumbName="YouTube"
      heroKicker="Для YouTube и длинных видео"
      heroTitle="YouTube снова в полном качестве"
      heroSubtitle="Скачайте приложение, нажмите «Подключить» — и видео идут в полном качестве, без «крутилки». Проверьте бесплатно, 5 дней без карты."
      scenarioTitle="Как дойти до первого видео"
      scenarioBody="Никаких настроек и профилей: приложение само делает то, что нужно."
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
    />
  );
}
