import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "Быстрый VPN на телефон | POKROV VPN",
  "Быстрый старт для телефона: приложение, 5 дней теста и понятный маршрут на Android без пустых технических переходов.",
  {
    path: "/bystryy-vpn-na-telefon/",
    keywords: ["быстрый vpn на телефон", "vpn на телефон", "впн на телефон", "vpn android"],
  },
);

export default function FastPhoneVpnPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "VPN на телефон", path: "/bystryy-vpn-na-telefon/" },
        ])}
      />
      <MarketingLanding
        pagePath="/bystryy-vpn-na-telefon/"
        heroKicker="Быстрый старт для телефона"
        heroTitle="VPN на телефон без долгой настройки"
        heroSubtitle="Если нужен быстрый мобильный старт, начните с приложения, включите тест на 5 дней и только потом решайте, хотите ли продлевать доступ."
        scenarioTitle="Что важно именно для телефона"
        scenarioBody="На мобильном сценарии важны короткий старт, предсказуемый маршрут и минимум ручных действий после первой установки."
        scenarioCards={[
          {
            eyebrow: "Мобильный старт",
            glyph: "arc",
            title: "Один короткий путь до первого подключения",
            desc: "Android-приложение сразу ведёт к реальному тесту, без прыжков по техническим ссылкам и без ручного импорта как основного сценария.",
          },
          {
            eyebrow: "Повседневный режим",
            glyph: "signal",
            title: "Проверяете сервис там, где пользуетесь телефоном каждый день",
            desc: "Открываете привычные приложения и спокойно смотрите, подходит ли маршрут под ваш ритм — только потом возвращаетесь к вопросу продления.",
          },
          {
            eyebrow: "Дальше без суеты",
            glyph: "route",
            title: "Кабинет и Telegram остаются запасным контуром",
            desc: "Продление, бонус и поддержка остаются под рукой, но сам продукт начинается именно с мобильного приложения.",
          },
        ]}
        clusterTitle="Когда нужен VPN на телефоне"
        clusterBody="Эта страница отвечает на мобильный сценарий и аккуратно ведёт в приложение, кабинет и checkout-маршрут без смешивания смыслов."
      />
    </>
  );
}
