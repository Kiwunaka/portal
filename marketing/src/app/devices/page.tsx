import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getSeoPage } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.devices);

export const metadata = buildMarketingMetadata(
  seoPage.title,
  seoPage.description,
  {
    path: MARKETING_CANONICAL_PATHS.devices,
  },
);

export default function DevicesPage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.devices}
      breadcrumbName="Устройства"
      heroKicker="Телефон + компьютер"
      heroTitle="Один аккаунт на все устройства"
      heroSubtitle="Android и Windows в одном аккаунте: до 5 устройств на основных тарифах. Подключили телефон — компьютер добавляется в пару кликов."
      scenarioTitle="Как это устроено"
      scenarioBody="Никакой отдельной оплаты за каждое устройство."
      scenarioCards={[
        {
          eyebrow: "Одна подписка",
          title: "До 5 устройств вместе",
          desc: "Телефон, ноутбук, планшет на Android — основной тариф покрывает всё сразу.",
        },
        {
          eyebrow: "Всё видно",
          title: "Устройства — в кабинете",
          desc: "Какие устройства подключены и когда заканчивается срок — видно в кабинете и приложении.",
        },
        {
          eyebrow: "Честный старт",
          title: "Сначала бесплатно",
          desc: "5 дней без карты, чтобы проверить связь на всех своих устройствах до оплаты.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
