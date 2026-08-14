import { HeroVisual } from "./hero-visual";
import { Button } from "../ui/button";
import { Chip } from "../ui/chip";
import { getCopyText, getSharedProductFacts, getTariffPlans } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getPokrovPublicConfig } from "../../lib/pokrov";
import { PlatformDownloadAction } from "./platform-download-action";

export function Hero() {
  const facts = getSharedProductFacts();
  const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
  const startPlan = getTariffPlans().find((plan) => plan.is_active) || null;
  const startPrice = startPlan ? `${startPlan.amount_rub} ₽` : "99 ₽";

  const factItems = [
    {
      title: getCopyText("marketing.home.hero.fact_trial.title", `${facts.trial.days} дней`),
      text: getCopyText("marketing.home.hero.fact_trial.text", "за 0 ₽, без карты"),
      href: `${MARKETING_CANONICAL_PATHS.checkout}?plan=start_99`,
    },
    {
      title: getCopyText("marketing.home.hero.fact_price.title", `от ${startPrice}`),
      text: getCopyText("marketing.home.hero.fact_price.text", "за полный месяц"),
    },
    {
      title: getCopyText("marketing.home.hero.fact_platforms.title", "Android + Windows"),
      text: getCopyText("marketing.home.hero.fact_platforms.text", "телефон + компьютер"),
    },
    {
      title: getCopyText("marketing.home.hero.fact_devices.title", "до 5 устройств"),
      text: getCopyText("marketing.home.hero.fact_devices.text", "на основных тарифах"),
    },
  ];

  return (
    <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-12 pb-16 sm:px-6 sm:pt-16 sm:pb-24 lg:grid-cols-[1.15fr_1fr]">
      <div className="flex flex-col items-start gap-6">
        <Chip>
          <span className="size-1.5 rounded-full bg-brand" />
          {getCopyText("marketing.home.hero.kicker", "POKROV VPN · Android + Windows")}
        </Chip>
        <h1 className="font-display text-[2.5rem] leading-[1.08] font-extrabold tracking-[-0.01em] text-ink sm:text-[3.25rem] lg:text-[3.5rem]">
          {getCopyText("marketing.home.hero.title", "YouTube, TikTok и ChatGPT — одной кнопкой")}
        </h1>
        <p className="max-w-lg text-lg leading-relaxed text-ink-soft">
          {getCopyText(
            "marketing.home.hero.subtitle",
            "POKROV для Android и Windows. 5 дней бесплатно, карта не нужна.",
          )}
        </p>
        <div className="flex flex-wrap gap-3">
          <PlatformDownloadAction
            initialAndroidUrl={config.androidApkUrl}
            initialWindowsUrl={config.windowsExeUrl}
          />
          <Button href="/#how-it-works" size="lg" variant="secondary">
            {getCopyText("marketing.home.hero.secondary_cta", "Как это работает")}
          </Button>
        </div>
        <div className="mt-2 grid w-full max-w-lg grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
          {factItems.map((item) => {
            const content = (
              <>
                <span className="text-[0.9375rem] font-bold text-ink">{item.title}</span>
                <span className="text-[0.8125rem] text-ink-soft">{item.text}</span>
              </>
            );
            return (
              <div key={item.title} className="border-l-2 border-brand-soft pl-3">
                {item.href ? (
                  <a
                    href={item.href}
                    aria-label={`${item.title}: выбрать срок доступа`}
                    className="flex min-h-11 flex-col justify-center gap-0.5 rounded-r-lg no-underline outline-none transition-colors hover:bg-brand-soft focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
                  >
                    {content}
                  </a>
                ) : (
                  <div className="flex min-h-11 flex-col justify-center gap-0.5">{content}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <HeroVisual />
    </section>
  );
}
