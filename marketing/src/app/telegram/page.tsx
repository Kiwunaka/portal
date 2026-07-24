import { IntentLanding } from "../../components/intent/intent-landing";
import {
  buildMarketingMetadata,
  MARKETING_CANONICAL_PATHS,
  PAID_REWARDS_MARKETING_COPY,
  PAID_REWARDS_MARKETING_ENABLED,
} from "../../lib/marketing-site";
import { getSeoPage, TELEGRAM_START_PROMISE } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.telegram);

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
      heroKicker="5 дней в приложении + 5 дней за Telegram"
      heroTitle="Заберите до 10 дней POKROV на старте"
      heroSubtitle={TELEGRAM_START_PROMISE}
      scenarioTitle="Одна подписка на канал — ещё 5 дней к бесплатному старту"
      scenarioBody="Плюс обновления сервиса и быстрый вход в поддержку."
      scenarioCards={[
        {
          eyebrow: "Ещё 5 дней",
          title: "Удвойте время на проверку POKROV",
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
    />
  );
}
