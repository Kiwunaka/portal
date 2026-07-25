import { HeroVisual } from "./hero-visual";
import { Button } from "../ui/button";
import { Chip } from "../ui/chip";
import { getCopyText, getSharedProductFacts, getTariffPlans } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export function Hero() {
  const facts = getSharedProductFacts();
  const startPlan = getTariffPlans().find((plan) => plan.is_active) || null;
  const startPrice = startPlan ? `${startPlan.amount_rub} ₽` : "99 ₽";

  const factItems = [
    {
      title: getCopyText("marketing.home.hero.fact_trial.title", `${facts.trial.days} дней`),
      text: getCopyText("marketing.home.hero.fact_trial.text", "за 0 ₽, без карты"),
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
          {getCopyText("marketing.home.hero.title", "Открывайте привычные сервисы")}
        </h1>
        <p className="max-w-lg text-lg leading-relaxed text-ink-soft">
          {getCopyText(
            "marketing.home.hero.subtitle",
            "Быстрый VPN для YouTube, TikTok, ChatGPT, соцсетей и сайтов. 5 дней бесплатно без карты. Затем — безлимитный трафик от 99 ₽ и до 5 устройств.",
          )}
        </p>
        <div className="flex flex-wrap gap-3">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            {getCopyText("marketing.home.hero.primary_cta", "Попробовать бесплатно")}
          </Button>
          <Button href="/#how-it-works" size="lg" variant="secondary">
            {getCopyText("marketing.home.hero.secondary_cta", "Как это работает")}
          </Button>
        </div>
        <dl className="mt-2 grid w-full max-w-lg grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
          {factItems.map((item) => (
            <div key={item.title} className="flex flex-col gap-0.5 border-l-2 border-brand-soft pl-3">
              <dt className="text-[0.9375rem] font-bold text-ink">{item.title}</dt>
              <dd className="m-0 text-[0.8125rem] text-ink-soft">{item.text}</dd>
            </div>
          ))}
        </dl>
      </div>
      <HeroVisual />
    </section>
  );
}
