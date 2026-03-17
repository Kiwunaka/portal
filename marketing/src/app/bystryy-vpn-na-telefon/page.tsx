import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "Быстрый VPN на телефон | PORTAL",
  "Быстрый VPN на телефон: Telegram-бот, тест 3 дня, подключение на Android и iPhone без сложной настройки.",
);

export default function FastVpnPhonePage() {
  return (
    <MarketingLanding
      heroKicker="SEO landing • быстрый VPN на телефон"
      heroTitle="Быстрый VPN на телефон без долгой настройки и холодного платёжного экрана"
      heroSubtitle="Подходит для сценария, когда человек ищет быстрый VPN на Android или iPhone и хочет сначала убедиться, что всё запускается, а уже потом платить."
      clusterTitle="Кластер вокруг мобильного входа"
      clusterBody="Мобильные SEO-запросы хорошо сочетаются с bot-first воронкой: переход из поиска, запуск теста, подключение приложения и короткая дорога до апгрейда."
    />
  );
}
