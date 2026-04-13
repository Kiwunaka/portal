import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Telegram и служба заботы | POKROV Network",
  "Telegram как быстрый помощник, связь с экспертами и забота о пользователях POKROV Network.",
  {
    path: "/vpn-telegram-bot/",
    keywords: ["ускоритель в телеграм", "помощь по сети", "телеграм бот для интернета", "pokrov сеть бот"],
  },
);

export default function VpnTelegramBotPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV Network", path: "/" },
          { name: "Telegram и служба заботы", path: "/vpn-telegram-bot/" },
        ])}
      />
      <MarketingLanding
        pagePath="/vpn-telegram-bot/"
        heroKicker="Telegram как забота, а не замена"
        heroTitle="Telegram как быстрый помощник POKROV Network"
        heroSubtitle="Наш бот помогает быстро решить любой вопрос в личном кабинете или через службу поддержки. Весь основной опыт разгона интернета остаётся внутри приложения."
        scenarioTitle="Почему Telegram удобен для помощи"
        scenarioBody="Мы используем Telegram только там, где он приносит реальную пользу: для бонусов, заботы о пользователях и восстановления доступа."
        scenarioCards={[
          {
            eyebrow: "Награда за канал",
            glyph: "signal",
            title: "Получайте бонусы за участие в жизни сообщества",
            desc: "После привязки аккаунта можно получить +10 дней к ускорению — это наша благодарность тем, кто с нами.",
          },
          {
            eyebrow: "Служба экспертов",
            glyph: "shield",
            title: "Команда заботы всегда под рукой",
            desc: "Если возникли вопросы по скорости или оплате, Telegram — самый быстрый способ получить человеческий ответ.",
          },
          {
            eyebrow: "Продолжение сценария",
            glyph: "route",
            title: "Бот помогает, когда это действительно нужно",
            desc: "Например, если вы возвращаетесь к покупке или восстанавливаете настройки, Telegram становится удобным вторым каналом связи.",
          },
        ]}
        clusterTitle="Похожие сценарии"
        clusterBody="Узнайте больше о том, как наша сеть помогает в ежедневных задачах на телефоне и компьютере."
      />
    </>
  );
}
