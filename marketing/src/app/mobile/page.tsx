import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getSeoPage } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.mobile);

export const metadata = buildMarketingMetadata(
  seoPage.title,
  seoPage.description,
  {
    path: MARKETING_CANONICAL_PATHS.mobile,
  },
);

export default function MobilePage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.mobile}
      breadcrumbName="На телефон"
      heroKicker="VPN на Android · 5 дней за 0 ₽"
      heroTitle="Верните нужные сервисы на телефон одной кнопкой"
      heroSubtitle="Скачайте официальный APK, нажмите «Подключить» и проверьте YouTube, TikTok и другие приложения. 5 дней бесплатно, карта не нужна."
      scenarioTitle="Почему POKROV — сильный выбор для телефона"
      scenarioBody="Быстрый старт, автоматический маршрут и весь доступ в одном аккаунте."
      scenarioCards={[
        {
          eyebrow: "5 дней за 0 ₽",
          title: "Скачали — нажали — проверили",
          desc: "Кабинет выдаёт официальный APK, приложение выбирает маршрут. Банковская карта не нужна.",
        },
        {
          eyebrow: "Автоматический режим",
          title: "Российские сайты — напрямую",
          desc: "Режим «всё, кроме РУ» направляет российские сервисы по прямому маршруту.",
        },
        {
          eyebrow: "Один аккаунт",
          title: "Срок, устройства и продление под рукой",
          desc: "Видите остаток доступа, подключённые устройства и тариф без поиска по чатам.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
