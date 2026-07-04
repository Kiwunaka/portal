import { Reveal, Stagger } from "../motion/reveal";
import { StepMiniIllustration } from "../illustrations/step-mini";
import { Button } from "../ui/button";
import { SectionHeading } from "../ui/section-heading";
import { StepCard } from "../ui/step-card";
import { getCopyText, getSharedProductFacts } from "../../lib/pokrov";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";

export function Steps() {
  const facts = getSharedProductFacts();

  const steps = [
    {
      title: getCopyText("marketing.home.steps.download.title", "Скачайте приложение"),
      text: getCopyText(
        "marketing.home.steps.download.text",
        "Android или Windows — файл весит немного, установка занимает минуту.",
      ),
      variant: "download" as const,
    },
    {
      title: getCopyText("marketing.home.steps.connect.title", "Нажмите «Подключить»"),
      text: getCopyText(
        "marketing.home.steps.connect.text",
        "Всё уже настроено: приложение само выберет лучший маршрут.",
      ),
      variant: "connect" as const,
    },
    {
      title: getCopyText("marketing.home.steps.done.title", "Готово"),
      text: getCopyText(
        "marketing.home.steps.done.text",
        `${facts.trial.days} бесплатных дней уже идут — карта для этого не нужна.`,
      ),
      variant: "done" as const,
    },
  ];

  return (
    <section id="how-it-works" className="scroll-mt-20 border-y border-line bg-canvas-alt">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
        <Reveal>
          <SectionHeading
            kicker={getCopyText("marketing.home.steps.kicker", "Как это работает")}
            title={getCopyText("marketing.home.steps.title", "Три шага — и всё открывается")}
            sub={getCopyText(
              "marketing.home.steps.sub",
              "Никаких профилей, ключей и настроек. Мы уже всё сделали за вас.",
            )}
          />
        </Reveal>
        <div className="grid gap-4 md:grid-cols-3">
          <Stagger>
            {steps.map((step, index) => (
              <StepCard
                key={step.title}
                index={index + 1}
                title={step.title}
                text={step.text}
                illustration={<StepMiniIllustration variant={step.variant} />}
                className="h-full"
              />
            ))}
          </Stagger>
        </div>
        <Reveal className="mt-10 flex justify-center">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            {getCopyText("marketing.home.steps.cta", "Начать бесплатно")}
          </Button>
        </Reveal>
      </div>
    </section>
  );
}
