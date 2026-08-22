import { Reveal } from "../motion/reveal";
import { Button } from "../ui/button";
import {
  CANONICAL_NEWS_CHANNEL_URL,
  getCopyText,
  getSharedProductFacts,
} from "../../lib/pokrov";

export function TelegramBonus() {
  const facts = getSharedProductFacts();

  return (
    <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6 sm:pb-24">
      <Reveal>
        <div className="flex flex-col items-start gap-6 rounded-(--radius-panel) border border-line bg-surface p-7 shadow-soft sm:flex-row sm:items-center sm:justify-between sm:p-9">
          <div className="flex items-center gap-5">
            <span
              aria-hidden="true"
              className="font-display flex size-16 shrink-0 items-center justify-center rounded-(--radius-card) bg-brand-soft text-[1.375rem] font-extrabold text-brand"
            >
              +{facts.telegram_reward.days}
            </span>
            <div className="flex flex-col gap-1">
              <h3 className="font-display text-[1.25rem] font-bold text-ink">
                {getCopyText(
                  "marketing.home.telegram.title",
                  `Доведите бесплатный старт до ${facts.trial.days + facts.telegram_reward.days} дней`,
                )}
              </h3>
              <p className="max-w-lg text-[0.9375rem] leading-relaxed text-ink-soft">
                {getCopyText(
                  "marketing.home.telegram.text",
                  `Привяжите Telegram, подпишитесь на официальный канал и заберите ещё ${facts.telegram_reward.days} дней в приложении — оплата для этого не нужна. Там же публикуем обновления и статусы работы.`,
                  { telegram_reward_days: facts.telegram_reward.days },
                )}
              </p>
            </div>
          </div>
          <Button
            href={CANONICAL_NEWS_CHANNEL_URL}
            variant="secondary"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            {getCopyText(
              "marketing.home.telegram.cta",
              `Забрать +${facts.telegram_reward.days} дней`,
              { telegram_reward_days: facts.telegram_reward.days },
            )}
          </Button>
        </div>
      </Reveal>
    </section>
  );
}
