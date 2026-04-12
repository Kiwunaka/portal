import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Telegram и служба заботы | POKROV VPN",
  "Telegram как запасной путь, служба заботы и продолжение сценария после входа в приложение или кабинет.",
  {
    path: "/vpn-telegram-bot/",
    keywords: ["vpn telegram bot", "telegram vpn bot", "vpn telegram", "pokrov telegram bot"],
  },
);

export default function VpnTelegramBotPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "Telegram и служба заботы", path: "/vpn-telegram-bot/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-telegram-bot/"
        heroKicker="Telegram как продолжение, а не замена"
        heroTitle="Telegram как быстрый резервный маршрут POKROV VPN"
        heroSubtitle="Бот помогает продолжить сценарий, если нужен личный checkout-маршрут, поддержка или восстановление доступа. Но основной публичный вход в продукт остаётся через приложение."
        scenarioTitle="Когда Telegram действительно нужен"
        scenarioBody="Эта страница не делает Telegram обязательным. Она объясняет ровно те случаи, где он полезен: бонус, продолжение оплаты, поддержка и восстановление."
        scenarioCards={[
          {
            eyebrow: "Бонус за канал",
            glyph: "signal",
            title: "Telegram нужен для награды, а не для первого запуска",
            desc: "После привязки аккаунта можно получить +10 дней, но продукт остаётся app-first и не заставляет начинать с бота.",
          },
          {
            eyebrow: "Поддержка",
            glyph: "shield",
            title: "Служба заботы уже встроена в маршрут",
            desc: "Если нужен резервный путь или помощь по оплате, Telegram остаётся самым быстрым человеческим входом в поддержку.",
          },
          {
            eyebrow: "Продолжение сценария",
            glyph: "route",
            title: "Бот помогает продолжить, когда это действительно нужно",
            desc: "Например, если вы возвращаетесь к покупке или восстанавливаете доступ, Telegram становится удобным вторым контуром.",
          },
        ]}
        clusterTitle="Похожие сценарии"
        clusterBody="Страница усиливает Telegram-запросы и при этом аккуратно возвращает пользователя к app-first логике релиза."
      />
    </>
  );
}
