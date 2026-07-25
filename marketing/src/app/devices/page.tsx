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
      heroKicker="До 5 устройств · Android + Windows"
      heroTitle="Один VPN на телефон и компьютер — без лишних подписок"
      heroSubtitle="Подключите до 5 устройств на основных тарифах POKROV. Сначала проверьте всё 5 дней бесплатно, затем выберите срок от 99 ₽."
      scenarioTitle="Один аккаунт закрывает все основные устройства"
      scenarioBody="Не покупайте отдельный VPN для каждого телефона и компьютера."
      scenarioCards={[
        {
          eyebrow: "Один тариф",
          title: "До 5 устройств вместе",
          desc: "Android-телефон, планшет и Windows-компьютер подключаются к одному аккаунту на основных тарифах.",
        },
        {
          eyebrow: "Полный контроль",
          title: "Все устройства — в кабинете",
          desc: "Смотрите подключённые устройства, остаток срока и продление в одном месте.",
        },
        {
          eyebrow: "Проверка — 0 ₽",
          title: "Сначала 5 дней бесплатно",
          desc: "Проверьте POKROV на своих устройствах до оплаты. Банковская карта не нужна.",
        },
      ]}
      seoPage={seoPage}
    />
  );
}
