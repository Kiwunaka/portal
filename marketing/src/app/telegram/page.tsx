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
      heroKicker="Бонус и поддержка"
      heroTitle="До 10 дней на старте"
      heroSubtitle={TELEGRAM_START_PROMISE}
      scenarioTitle="Что даёт Telegram"
      scenarioBody="Три причины подписаться — все честные."
      scenarioCards={[
        {
          eyebrow: "Бонус",
          title: "+5 дней после Telegram",
          desc: "Привяжите Telegram, подпишитесь на канал и подтвердите подписку в аккаунте.",
        },
        {
          eyebrow: "Поддержка",
          title: "Живой человек в чате",
          desc: "Установка, оплата, восстановление доступа — поддержка отвечает по делу, а не скриптами.",
        },
        {
          eyebrow: "Новости",
          title: "Статусы работы сервиса",
          desc: "Если что-то меняется — маршруты, версии, акции — вы узнаете первым в канале.",
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
