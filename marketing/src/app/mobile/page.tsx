import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "POKROV на телефоне | 5 дней проверки",
  "Установите POKROV на Android, нажмите «Попробовать 5 дней» и проверьте доступ в привычных мобильных задачах.",
  {
    path: MARKETING_CANONICAL_PATHS.mobile,
    keywords: ["доступ на телефон", "android pokrov", "приложение android", "мобильный старт"],
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
      <div className="lp-route-shell lp-route-shell--intent lp-route-shell--mobile">
        <MarketingLanding
          pagePath={MARKETING_CANONICAL_PATHS.mobile}
          heroKicker="POKROV на телефоне"
          heroTitle="Android: скачайте приложение, попробуйте 5 дней, затем решите про ключ"
          heroSubtitle="Для телефона важен короткий путь: скачать приложение, включить 5 дней проверки и понять, подходит ли POKROV в ваших обычных задачах. Покупка нужна только когда вы готовы продолжить."
          scenarioTitle="Что важно на телефоне"
          scenarioBody="Мобильный старт ведёт к приложению, понятным действиям и поддержке рядом, если установка или первый запуск пошли не так."
          scenarioCards={[
            {
              eyebrow: "Установка",
              glyph: "arc",
              title: "Один короткий путь до проверки",
              desc: "Android-приложение доводит до реального опыта без лишних переходов и сложных настроек.",
            },
            {
              eyebrow: "Повседневно",
              glyph: "signal",
              title: "Проверяете связь там, где живёте каждый день",
              desc: "Открываете привычные приложения и сами видите, насколько спокойно всё работает.",
            },
            {
              eyebrow: "Дальше",
              glyph: "route",
              title: "Кабинет нужен после первого опыта",
              desc: "Продление, ключ доступа и поддержка ждут в кабинете, когда вы уже поняли, что POKROV вам подходит.",
            },
          ]}
          clusterTitle="Для мобильного старта"
          clusterBody="Отсюда удобно перейти к установке на Android, видео, устройствам и Telegram."
        />
      </div>
    </>
  );
}
