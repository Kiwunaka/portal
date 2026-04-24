import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Telegram +10 дней | POKROV",
  "Как Telegram помогает в POKROV: бонус +10 дней, поддержка, новости и восстановление доступа без замены приложения.",
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
          heroKicker="Telegram +10 дней"
          heroTitle="Telegram рядом для бонуса, поддержки и восстановления"
          heroSubtitle="Основной старт остаётся в приложении. Telegram помогает забрать +10 дней, перейти к поддержке, увидеть новости и вернуться к доступу, если что-то пошло не так."
          scenarioTitle="Когда нужен Telegram"
          scenarioBody="Telegram полезен там, где нужен человек, короткое уведомление или бонус за участие в канале. Для первого запуска он не обязателен."
          scenarioCards={[
            {
              eyebrow: "+10 дней",
              glyph: "signal",
              title: "Бонус за канал",
              desc: "После привязки Telegram и подписки на канал можно забрать +10 дней к доступу.",
            },
            {
              eyebrow: "Поддержка",
              glyph: "shield",
              title: "Человеческий ответ без лишнего круга",
              desc: "Если появились вопросы по скорости, доступу или оплате, Telegram остаётся самым быстрым способом поговорить с командой.",
            },
            {
              eyebrow: "Восстановление",
              glyph: "route",
              title: "Бот помогает только по делу",
              desc: "Например, когда нужно вернуться к кабинету, восстановить доступ или быстро перейти к нужному шагу.",
            },
          ]}
          clusterTitle="Рядом с Telegram"
          clusterBody="Посмотрите страницы про телефон, устройства и видео, если хотите начать с приложения, а не с чата."
        />
      </div>
    </>
  );
}
