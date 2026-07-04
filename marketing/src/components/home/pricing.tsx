import { Reveal, Stagger } from "../motion/reveal";
import { Button } from "../ui/button";
import { PriceCard } from "../ui/price-card";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText, getSharedProductFacts, getTariffPlans } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

function monthsFromDays(days: number): number {
  return Math.max(1, Math.round(days / 30.4));
}

function formatDuration(days: number): string {
  const months = monthsFromDays(days);
  if (days <= 31) return "за 30 дней";
  const word = months >= 5 ? "месяцев" : "месяца";
  return `за ${months} ${word}`;
}

export function Pricing() {
  const facts = getSharedProductFacts();
  const plans = getTariffPlans()
    .filter((plan) => plan.is_active)
    .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0));

  const yearPlan = plans.find((plan) => Number(plan.duration_days) >= 360);

  return (
    <section id="pricing" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 sm:py-24">
      <Reveal>
        <SectionHeading
          kicker={getCopyText("marketing.home.pricing.kicker", "Цены")}
          title={getCopyText("marketing.home.pricing.title", "Сначала бесплатно. Потом — честно")}
          sub={getCopyText(
            "marketing.home.pricing.sub",
            "Оплата разовым ключом: заплатили за срок — пользуетесь. Автосписаний нет, отменять нечего.",
          )}
        />
      </Reveal>

      <Reveal>
        <div className="mb-8 flex flex-col items-start justify-between gap-5 rounded-(--radius-panel) border border-line-strong bg-brand-soft p-7 sm:flex-row sm:items-center sm:p-8">
          <div className="flex flex-col gap-1.5">
            <h3 className="font-display text-[1.375rem] font-bold text-ink">
              {getCopyText("marketing.home.pricing.trial.title", `Первые ${facts.trial.days} дней — бесплатно`)}
            </h3>
            <p className="max-w-md text-[0.9375rem] leading-relaxed text-ink-soft">
              {getCopyText(
                "marketing.home.pricing.trial.text",
                "Скачайте приложение и проверьте всё на своих сервисах. Карта не нужна.",
              )}
            </p>
          </div>
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg" className="shrink-0">
            {getCopyText("marketing.home.pricing.trial.cta", "Начать бесплатно")}
          </Button>
        </div>
      </Reveal>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stagger>
          {plans.map((plan) => {
            const months = monthsFromDays(Number(plan.duration_days));
            const perMonth = months > 1 ? Math.round(Number(plan.amount_rub) / months) : null;
            const featured = yearPlan ? plan.code === yearPlan.code : false;
            const deviceLimit = Number(plan.device_limit || 1);
            return (
              <PriceCard
                key={plan.code}
                title={plan.label}
                price={`${plan.amount_rub} ₽`}
                durationNote={formatDuration(Number(plan.duration_days))}
                perMonthNote={perMonth ? `это ${perMonth} ₽ в месяц` : undefined}
                deviceNote={
                  deviceLimit > 1
                    ? `до ${deviceLimit} устройств одновременно`
                    : "1 устройство — чтобы попробовать всерьёз"
                }
                featured={featured}
                featuredNote={getCopyText("marketing.home.pricing.featured_note", "Выгоднее всего")}
                ctaHref={`${MARKETING_CANONICAL_PATHS.checkout}?plan=${encodeURIComponent(plan.code)}`}
                ctaLabel={getCopyText("marketing.home.pricing.cta", "Выбрать")}
                className="h-full"
              />
            );
          })}
        </Stagger>
      </div>

      <Reveal>
        <p className="mt-8 text-center text-[0.8125rem] text-ink-muted">
          {getCopyText(
            "marketing.home.pricing.note",
            "Все цены в рублях. Код активации можно применить в приложении или кабинете.",
          )}
        </p>
      </Reveal>
    </section>
  );
}
