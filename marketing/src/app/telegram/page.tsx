import { IntentLanding } from "../../components/intent/intent-landing";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Telegram-бонус +10 дней и поддержка | POKROV",
  "Подпишитесь на Telegram-канал POKROV и получите +10 дней доступа. Там же — живая поддержка и новости сервиса.",
  {
    path: MARKETING_CANONICAL_PATHS.telegram,
    keywords: ["telegram pokrov", "поддержка pokrov", "бонус telegram", "быстрая поддержка"],
  },
);

export default function TelegramPage() {
  return (
    <IntentLanding
      pagePath={MARKETING_CANONICAL_PATHS.telegram}
      breadcrumbName="Telegram"
      heroKicker="Бонус и поддержка"
      heroTitle="+10 дней за подписку на канал"
      heroSubtitle="Telegram не обязателен для старта, но полезен: бонус +10 дней, живая поддержка и новости о работе сервиса — всё в одном месте."
      scenarioTitle="Что даёт Telegram"
      scenarioBody="Три причины подписаться — все честные."
      scenarioCards={[
        {
          eyebrow: "Бонус",
          title: "+10 дней к доступу",
          desc: "Подпишитесь на канал и заберите бонус в приложении — он прибавится к текущему сроку.",
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
      ]}
    />
  );
}
