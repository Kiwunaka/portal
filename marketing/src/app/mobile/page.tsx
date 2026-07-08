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
      heroKicker="Быстрый старт на телефоне"
      heroTitle="Поставьте на телефон — и забудьте"
      heroSubtitle="Android-приложение ставится за минуту и дальше просто работает: без профилей, ключей и инструкций на полчаса."
      scenarioTitle="Почему на телефоне это удобно"
      scenarioBody="Всё, что нужно каждый день, — уже в приложении."
      scenarioCards={[
        {
          eyebrow: "Установка за минуту",
          title: "Скачали — подключили",
          desc: "Файл выдаёт кабинет, приложение само выбирает маршрут. Первые 5 дней бесплатно.",
        },
        {
          eyebrow: "Живёт в фоне",
          title: "Работает и не мешает",
          desc: "Подключение держится в фоне, а российские приложения работают напрямую.",
        },
        {
          eyebrow: "Всё под рукой",
          title: "Срок и продление — в приложении",
          desc: "Сколько дней осталось и как продлить — видно прямо на экране аккаунта.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
