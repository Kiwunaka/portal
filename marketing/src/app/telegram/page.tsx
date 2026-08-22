import { IntentLanding } from "../../components/intent/intent-landing";
import {
  buildMarketingMetadata,
  MARKETING_CANONICAL_PATHS,
  PAID_REWARDS_MARKETING_COPY,
  PAID_REWARDS_MARKETING_ENABLED,
} from "../../lib/marketing-site";
import { getSharedProductFacts } from "../../lib/pokrov";
import { getSeoPage, TELEGRAM_START_PROMISE } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.telegram);
const productFacts = getSharedProductFacts();
const trialDays = productFacts.trial.days;
const telegramRewardDays = productFacts.telegram_reward.days;

export const metadata = buildMarketingMetadata(
  seoPage.title,
  seoPage.description,
  {
    path: MARKETING_CANONICAL_PATHS.telegram,
  },
);

export default function TelegramPage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.telegram}
      breadcrumbName="Telegram"
      heroKicker={`${trialDays} дней без карты · ещё +${telegramRewardDays} за Telegram без оплаты`}
      heroTitle={`Получите ${trialDays} дней бесплатно и ещё ${telegramRewardDays} за Telegram`}
      heroSubtitle={TELEGRAM_START_PROMISE}
      scenarioTitle={`Привязка Telegram, подписка на канал — и ещё ${telegramRewardDays} дней`}
      scenarioBody="Плюс обновления сервиса и быстрый вход в поддержку."
      scenarioCards={[
        {
          eyebrow: "Без оплаты",
          title: `Получите ещё ${telegramRewardDays} дней за Telegram`,
          desc: "Привяжите Telegram, подпишитесь на официальный канал и подтвердите подписку в аккаунте.",
        },
        {
          eyebrow: "Помощь",
          title: "Не останетесь один на один с настройкой",
          desc: "По установке, оплате и восстановлению можно открыть одно обращение и продолжить диалог в Telegram.",
        },
        {
          eyebrow: "Обновления",
          title: "Статусы, версии и акции в одном канале",
          desc: "Следите за изменениями маршрутов, новыми версиями и бонусными предложениями POKROV.",
        },
        ...(PAID_REWARDS_MARKETING_ENABLED
          ? [
              {
                eyebrow: "Для платной подписки",
                title: "Награды за активность",
                desc: PAID_REWARDS_MARKETING_COPY,
              },
            ]
          : []),
      ]}
      seoPage={seoPage}
      telegramBotCta
    />
  );
}
