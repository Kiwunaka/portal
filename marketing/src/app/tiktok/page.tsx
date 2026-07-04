import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "TikTok снова открывается | POKROV для Android и Windows",
  "POKROV возвращает TikTok: лента, лайки и загрузка роликов работают как раньше. 5 дней бесплатно без карты.",
  {
    path: MARKETING_CANONICAL_PATHS.tiktok,
    keywords: ["проверка tiktok", "tiktok не работает", "короткие ролики", "pokrov tiktok"],
  },
);

export default function TiktokPage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.tiktok}
      breadcrumbName="TikTok"
      heroKicker="Для TikTok и коротких роликов"
      heroTitle="TikTok снова открывается"
      heroSubtitle="Лента, лайки и загрузка своих роликов — как раньше. Скачайте приложение и проверьте бесплатно: 5 дней, карта не нужна."
      scenarioTitle="Как вернуть ленту за минуту"
      scenarioBody="Приложение уже настроено — остаётся установить и нажать одну кнопку."
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
    />
  );
}
