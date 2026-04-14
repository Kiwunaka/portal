import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "Мобильный старт | POKROV",
  "Быстрый старт для телефона: приложение, 5 дней теста и спокойный маршрут к стабильной сети на Android.",
  {
    path: MARKETING_CANONICAL_PATHS.mobile,
    keywords: ["быстрый интернет на телефон", "ускоритель на телефон", "android", "мобильный старт"],
  },
);

export default function MobilePage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "Мобильный старт", path: MARKETING_CANONICAL_PATHS.mobile },
        ])}
      />
      <MarketingLanding
        pagePath={MARKETING_CANONICAL_PATHS.mobile}
        heroKicker="Мобильный старт"
        heroTitle="Умная сеть на телефон без долгой настройки"
        heroSubtitle="Если нужен быстрый мобильный старт, начните с приложения, включите тест на 5 дней и почувствуйте разницу уже сегодня."
        scenarioTitle="Почему это удобно на телефоне"
        scenarioBody="В мобильном сценарии важны короткий путь к цели, стабильная связь и минимум ручных действий."
        scenarioCards={[
          {
            eyebrow: "Мобильный старт",
            glyph: "arc",
            title: "Один короткий шаг к быстрой сети",
            desc: "Android-приложение сразу ведёт к результату, без прыжков по техническим ссылкам и сложной настройки.",
          },
          {
            eyebrow: "Повседневный режим",
            glyph: "signal",
            title: "Проверяете связь там, где пользуетесь телефоном каждый день",
            desc: "Открываете любимые приложения и проверяете стабильность в привычных сценариях.",
          },
          {
            eyebrow: "Дальше без суеты",
            glyph: "route",
            title: "Удобный кабинет для управления",
            desc: "Полный контроль всегда под рукой в личном кабинете, когда вы решите, что скорость вас устраивает.",
          },
        ]}
        clusterTitle="Когда нужен быстрый старт на телефоне"
        clusterBody="Эта страница отвечает на мобильный сценарий и ведёт в приложение, кабинет и оплату без смешивания смыслов."
      />
    </>
  );
}
