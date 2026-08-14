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
      heroKicker="VPN для TikTok · 5 дней за 0 ₽"
      heroTitle="Верните TikTok: ленту, лайки и загрузку роликов"
      heroSubtitle="Скачайте POKROV, нажмите «Подключить» и проверьте TikTok на своём устройстве. 5 дней бесплатно, без карты и автосписаний."
      scenarioTitle="Вернуть ленту проще, чем искать новый VPN"
      scenarioBody="Приложение уже настроено: установите, нажмите одну кнопку и проверьте всё до оплаты."
      scenarioCards={[
        {
          eyebrow: "5 дней бесплатно",
          title: "Проверьте весь TikTok до оплаты",
          desc: "Лента, комментарии, лайки и тестовая загрузка ролика — на вашем телефоне и вашей сети.",
        },
        {
          eyebrow: "Телефон + компьютер",
          title: "Android и Windows в одном аккаунте",
          desc: "Основные тарифы позволяют подключить до 5 устройств без отдельной подписки на каждое.",
        },
        {
          eyebrow: "От 99 ₽",
          title: "Оплата разовая, выгода до 30%",
          desc: "Выберите короткий старт или длинный срок. Автосписаний нет — продление только по вашему действию.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
