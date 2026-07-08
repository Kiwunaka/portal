import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getSeoPage } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.tiktok);

export const metadata = buildMarketingMetadata(
  seoPage.title,
  seoPage.description,
  {
    path: MARKETING_CANONICAL_PATHS.tiktok,
  },
);

export default function TiktokPage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.tiktok}
      breadcrumbName="TikTok"
      heroKicker="Для TikTok и коротких роликов"
      heroTitle="Проверьте TikTok через POKROV"
      heroSubtitle="Лента, лайки и загрузка роликов проверяются на вашем устройстве. Скачайте приложение бесплатно: 5 дней, карта не нужна."
      scenarioTitle="Как вернуть ленту за минуту"
      scenarioBody="Приложение уже настроено: остаётся установить, нажать кнопку и проверить свой сценарий."
      scenarioCards={[
        {
          eyebrow: "Сначала проверка",
          title: "TikTok — до оплаты",
          desc: "5 бесплатных дней хватает, чтобы понять: лента грузится, ролики публикуются.",
        },
        {
          eyebrow: "На телефоне и ПК",
          title: "Android и Windows",
          desc: "Один аккаунт работает и на телефоне, и на компьютере.",
        },
        {
          eyebrow: "Без сюрпризов",
          title: "Оплата разовая",
          desc: "Никаких автосписаний: заплатили за срок — пользуетесь, продлевать или нет — решаете сами.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
