import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Telegram-бонус и поддержка | POKROV",
  "Telegram в POKROV: +10 дней за канал, поддержка и восстановление, пока основной старт остается в приложении.",
  {
    path: MARKETING_CANONICAL_PATHS.telegram,
    keywords: ["telegram pokrov", "поддержка pokrov", "бонус telegram", "команда поддержки"],
  },
);

export default function TelegramPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "Telegram и поддержка", path: MARKETING_CANONICAL_PATHS.telegram },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--telegram">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.telegram}
          heroKicker="Telegram как бонус и поддержка"
          heroTitle="Telegram дает +10 дней и быстрый контакт с поддержкой"
          heroSubtitle="Бот помогает быстро вернуться к кабинету, бонусу или поддержке. Основной опыт по-прежнему живёт внутри приложения и личного кабинета."
          scenarioTitle="Где Telegram помогает лучше всего"
          scenarioBody="Мы используем Telegram для бонусов, поддержки и восстановления доступа, но первый старт остается в приложении."
          scenarioCards={[
            {
              eyebrow: "Бонус за канал",
              glyph: "signal",
              title: "Плюс 10 дней за участие в сообществе",
              desc: "После привязки аккаунта можно получить +10 дней за официальный канал POKROV.",
            },
            {
              eyebrow: "Поддержка",
              glyph: "shield",
              title: "Человеческий ответ по установке и продлению",
              desc: "Если появились вопросы по скорости, доступу или оплате, Telegram остаётся самым быстрым способом поговорить с командой.",
            },
            {
              eyebrow: "Продолжение",
              glyph: "route",
              title: "Бот помогает только по делу",
              desc: "Например, когда вы возвращаетесь к покупке, восстанавливаете доступ или хотите быстро открыть нужное действие.",
            },
          ]}
          clusterTitle="Похожие задачи"
          clusterBody="Узнайте больше о том, как POKROV помогает в ежедневных задачах на телефоне и компьютере."
        />
      </div>
    </>
  );
}
