import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Быстрая сеть на телефон | POKROV Network",
  "Быстрый старт для телефона: приложение, 5 дней тест-драйва и идеальное качество связи на Android без пауз и долгого ожидания.",
  {
    path: "/bystryy-vpn-na-telefon/",
    keywords: ["быстрый интернет на телефон", "ускоритель на телефон", "оптимизатор на телефон", "стабильная сеть android"],
  },
);

export default function FastPhoneVpnPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV Network", path: "/" },
          { name: "Сеть на телефон", path: "/bystryy-vpn-na-telefon/" },
        ])}
      />
      <MarketingLanding
        pagePath="/bystryy-vpn-na-telefon/"
        heroKicker="Быстрый старт для телефона"
        heroTitle="Умная сеть на телефон без долгой настройки"
        heroSubtitle="Если нужен быстрый мобильный старт, начните с приложения, включите тест-драйв на 5 дней и почувствуйте магию скорости уже сегодня."
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
            desc: "Открываете любимые приложения и наслаждаетесь стабильностью — мы позаботимся о качестве маршрутов за вас.",
          },
          {
            eyebrow: "Дальше без суеты",
            glyph: "route",
            title: "Удобный кабинет для управления",
            desc: "Полный контроль всегда под рукой в личном кабинете, когда вы решите, что скорость вас устраивает.",
          },
        ]}
        clusterTitle="Когда нужна стабильная сеть на телефоне"
        clusterBody="Эта страница отвечает на мобильный сценарий и аккуратно ведёт в приложение, кабинет и checkout-маршрут без смешивания смыслов."
      />
    </>
  );
}
