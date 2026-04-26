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
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--telegram">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.telegram}
          heroKicker="Telegram как забота, а не замена"
          heroTitle="Telegram остаётся рядом, когда нужен человек"
          heroSubtitle="Бот помогает быстро вернуться к кабинету, бонусу или поддержке. Основной опыт по-прежнему живёт внутри приложения и личного кабинета."
          scenarioTitle="Почему Telegram удобен для помощи"
          scenarioBody="Мы используем Telegram только там, где он действительно полезен: для бонусов, спокойной поддержки и восстановления доступа."
          scenarioCards={[
            {
              eyebrow: "Бонус за канал",
              glyph: "signal",
              title: "Плюс 10 дней за участие в сообществе",
              desc: "После привязки аккаунта можно получить +10 дней — тихая благодарность тем, кто остаётся рядом с POKROV.",
            },
            {
              eyebrow: "Служба заботы",
              glyph: "shield",
              title: "Человеческий ответ без лишнего пути",
              desc: "Если появились вопросы по скорости, доступу или оплате, Telegram остаётся самым быстрым способом поговорить с командой.",
            },
            {
              eyebrow: "Продолжение сценария",
              glyph: "route",
              title: "Бот помогает только по делу",
              desc: "Например, когда вы возвращаетесь к покупке, восстанавливаете доступ или хотите быстро перейти к нужному шагу.",
            },
          ]}
          clusterTitle="Похожие сценарии"
          clusterBody="Узнайте больше о том, как POKROV помогает в ежедневных задачах на телефоне и компьютере, не меняя app-first логику."
        />
      </div>
    </>
  );
}
