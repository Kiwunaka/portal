"use client";

import { AnimatePresence, motion, useReducedMotion, useScroll, useMotionValueEvent } from "framer-motion";
import { useRef, useState } from "react";

import { AppPhoneIllustration, type AppPhoneVariant } from "../illustrations/app-phone";
import { AppWindowIllustration } from "../illustrations/app-window";
import { cn } from "../utils";

const EASE = [0.22, 1, 0.36, 1] as const;

export type ShowcaseSlide = {
  text: string;
  title: string;
  variant: AppPhoneVariant | "windows";
};

function SlideVisual({ variant }: { variant: ShowcaseSlide["variant"] }) {
  if (variant === "windows") {
    return <AppWindowIllustration className="mx-auto" />;
  }
  return <AppPhoneIllustration variant={variant} className="mx-auto" />;
}

export function ShowcaseScroller({
  heading,
  slides,
}: {
  heading: React.ReactNode;
  slides: ShowcaseSlide[];
}) {
  const reduceMotion = useReducedMotion();
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [active, setActive] = useState(0);

  const { scrollYProgress } = useScroll({
    target: trackRef,
    offset: ["start start", "end end"],
  });

  useMotionValueEvent(scrollYProgress, "change", (value) => {
    const index = Math.min(slides.length - 1, Math.max(0, Math.floor(value * slides.length)));
    setActive(index);
  });

  return (
    <section id="showcase" className="scroll-mt-20">
      {/* Desktop: sticky scroll-driven crossfade */}
      <div ref={trackRef} className="relative hidden lg:block" style={{ height: `${slides.length * 90}vh` }}>
        <div className="sticky top-16 flex h-[calc(100vh-4rem)] items-center">
          <div className="mx-auto grid w-full max-w-6xl grid-cols-[1fr_1.1fr] items-center gap-16 px-6">
            <div className="flex flex-col gap-8">
              {heading}
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {slides.map((slide, index) => (
                  <li key={slide.title}>
                    <div
                      className={cn(
                        "rounded-(--radius-card) border px-5 py-4 transition-[border-color,background-color,opacity] duration-300 ease-(--ease-apple)",
                        index === active
                          ? "border-line-strong bg-surface shadow-soft"
                          : "border-transparent opacity-55",
                      )}
                    >
                      <h3 className="text-[1.0625rem] font-semibold text-ink">{slide.title}</h3>
                      <p className="mt-1 text-[0.9375rem] leading-relaxed text-ink-soft">{slide.text}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative flex min-h-[520px] items-center justify-center">
              <AnimatePresence mode="popLayout" initial={false}>
                <motion.div
                  key={slides[active].variant}
                  initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 16, scale: 0.985 }}
                  animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
                  exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -16, scale: 0.985 }}
                  transition={{ duration: 0.32, ease: EASE }}
                  className="w-full"
                >
                  <SlideVisual variant={slides[active].variant} />
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile / tablet: snap carousel */}
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 sm:px-6 lg:hidden">
        {heading}
        <div className="-mx-4 flex snap-x snap-mandatory gap-6 overflow-x-auto px-4 pb-4 sm:-mx-6 sm:px-6">
          {slides.map((slide) => (
            <figure key={slide.title} className="m-0 flex w-[85%] max-w-xs shrink-0 snap-center flex-col gap-4">
              <SlideVisual variant={slide.variant} />
              <figcaption>
                <h3 className="text-base font-semibold text-ink">{slide.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-ink-soft">{slide.text}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
