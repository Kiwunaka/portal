import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Telegram и забота | POKROV",
  "Telegram как быстрый помощник, бонус и канал поддержки, пока основной опыт остаётся внутри приложения и кабинета.",
  {
    path: MARKETING_CANONICAL_PATHS.telegram,
    keywords: ["telegram pokrov", "поддержка pokrov", "бонус telegram", "служба заботы"],
  },
);

export default function TelegramPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "Telegram и служба заботы", path: MARKETING_CANONICAL_PATHS.telegram },
        ])}
      />
      <MarketingLanding
        pagePath={MARKETING_CANONICAL_PATHS.telegram}
        heroKicker="Telegram как забота, а не замена"
        heroTitle="Telegram как быстрый помощник POKROV"
        heroSubtitle="Наш бот помогает быстро решить вопрос в кабинете или через поддержку. Основной опыт остаётся внутри приложения."
        scenarioTitle="Почему Telegram удобен для помощи"
        scenarioBody="Мы используем Telegram только там, где он приносит реальную пользу: для бонусов, заботы о пользователях и восстановления доступа."
        scenarioCards={[
          {
            eyebrow: "Награда за канал",
            glyph: "signal",
            title: "Получайте бонусы за участие в жизни сообщества",
            desc: "После привязки аккаунта можно получить +10 дней — это наша благодарность тем, кто с нами.",
          },
          {
            eyebrow: "Служба заботы",
            glyph: "shield",
            title: "Команда всегда под рукой",
            desc: "Если возникли вопросы по скорости или оплате, Telegram — быстрый способ получить человеческий ответ.",
          },
          {
            eyebrow: "Продолжение сценария",
            glyph: "route",
            title: "Бот помогает, когда это действительно нужно",
            desc: "Например, если вы возвращаетесь к покупке или восстанавливаете настройки, Telegram становится удобным вторым каналом связи.",
          },
        ]}
        clusterTitle="Похожие сценарии"
        clusterBody="Узнайте больше о том, как POKROV помогает в ежедневных задачах на телефоне и компьютере."
      />
    </>
  );
}
