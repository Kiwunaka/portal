import JsonLd from "../../components/json-ld";
import MarketingLanding, { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";

export const metadata = buildMarketingMetadata(
  "POKROV на телефоне | 5 дней без возни",
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
          heroTitle="Android без возни: установили, нажали «Попробовать 5 дней», проверили"
          heroSubtitle="Для телефона важен короткий путь: скачать приложение, включить 5 дней проверки и понять, подходит ли POKROV в ваших обычных задачах."
          scenarioTitle="Что важно на телефоне"
          scenarioBody="Мобильная страница про быстрый старт, понятные действия и поддержку рядом, если установка или первый запуск пошли не так."
          scenarioCards={[
            {
              eyebrow: "Установка",
              glyph: "arc",
              title: "Один короткий путь до проверки",
              desc: "Android-приложение доводит до реального опыта без прыжков по ссылкам и сложных настроек.",
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
              title: "Кабинет нужен только после первого опыта",
              desc: "Продление, ключи и поддержка ждут в кабинете, когда вы уже поняли, что POKROV вам подходит.",
            },
          ]}
          clusterTitle="Для мобильного старта"
          clusterBody="Эта страница ведёт к установке на Android, а соседние страницы отдельно объясняют видео, устройства и Telegram."
        />
      </div>
    </>
  );
}
