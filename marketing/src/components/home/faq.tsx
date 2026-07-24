import { Reveal } from "../motion/reveal";
import { Accordion } from "../ui/accordion";
import { SectionHeading } from "../ui/section-heading";
import { getCopyText } from "../../lib/pokrov";
import { MARKETING_FAQ } from "../../lib/marketing-site";

export function Faq() {
  return (
    <section id="faq" className="scroll-mt-20 border-t border-line bg-canvas-alt">
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
        <Reveal>
          <SectionHeading
            kicker={getCopyText("marketing.home.faq.kicker", "Перед стартом")}
            title={getCopyText("marketing.home.faq.title", "Ответы, после которых можно подключаться")}
          />
        </Reveal>
        <Reveal>
          <Accordion items={MARKETING_FAQ} />
        </Reveal>
      </div>
    </section>
  );
}
