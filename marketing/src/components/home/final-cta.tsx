import { Reveal } from "../motion/reveal";
import { Button } from "../ui/button";
import { CANONICAL_SUPPORT_BOT_URL, getCopyText, getSharedProductFacts } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export function FinalCta() {
  const facts = getSharedProductFacts();

  return (
    <section className="bg-brand-soft">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-16 text-center sm:px-6 sm:py-24">
        <Reveal className="flex flex-col items-center gap-4">
          <h2 className="font-display max-w-2xl text-[2rem] leading-[1.12] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.5rem]">
            {getCopyText("marketing.home.final.title", "Подключите POKROV VPN за минуту")}
          </h2>
          <p className="max-w-lg text-base leading-relaxed text-ink-soft">
            {getCopyText(
              "marketing.home.final.sub",
              `YouTube, TikTok, ChatGPT и нужные сайты — одной кнопкой. ${facts.trial.days} дней бесплатно без карты, затем безлимитный трафик от 99 ₽.`,
            )}
          </p>
        </Reveal>
        <Reveal className="flex flex-wrap items-center justify-center gap-4">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            {getCopyText("marketing.home.final.cta", "Подключить VPN бесплатно")}
          </Button>
          <a
            href={CANONICAL_SUPPORT_BOT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[0.9375rem] font-semibold text-brand no-underline hover:text-brand-strong"
          >
            {getCopyText("marketing.home.final.support", "Помогите мне подключиться")}
          </a>
        </Reveal>
      </div>
    </section>
  );
}
