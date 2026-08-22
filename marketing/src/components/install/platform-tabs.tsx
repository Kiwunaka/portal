"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import { AnimatePresence, m, useReducedMotion } from "framer-motion";

import { StepMiniIllustration, type StepMiniVariant } from "../illustrations/step-mini";
import { StepCard } from "../ui/step-card";
import { cn } from "../utils";

export type InstallStep = {
  text: string;
  title: string;
  variant: StepMiniVariant;
};

export type InstallPlatform = {
  id: "android" | "windows";
  label: string;
  note?: string;
  steps: InstallStep[];
};

export function PlatformTabs({ platforms }: { platforms: InstallPlatform[] }) {
  const [activeId, setActiveId] = useState(platforms[0]?.id ?? "android");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const reduceMotion = useReducedMotion();
  const active = platforms.find((platform) => platform.id === activeId) ?? platforms[0];

  const selectTab = (index: number) => {
    const platform = platforms[index];
    if (!platform) return;
    setActiveId(platform.id);
    tabRefs.current[index]?.focus();
  };

  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const lastIndex = platforms.length - 1;
    const nextIndex =
      event.key === "ArrowRight"
        ? (index + 1) % platforms.length
        : event.key === "ArrowLeft"
          ? (index - 1 + platforms.length) % platforms.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? lastIndex
              : null;
    if (nextIndex === null || platforms.length === 0) return;
    event.preventDefault();
    selectTab(nextIndex);
  };

  return (
    <div className="flex flex-col gap-8">
      <div
        role="tablist"
        aria-label="Платформа"
        className="mx-auto flex rounded-full border border-line bg-canvas-alt p-1"
      >
        {platforms.map((platform, index) => {
          const selected = platform.id === active.id;
          return (
            <button
              key={platform.id}
              ref={(node) => {
                tabRefs.current[index] = node;
              }}
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`install-panel-${platform.id}`}
              id={`install-tab-${platform.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setActiveId(platform.id)}
              onKeyDown={(event) => handleTabKeyDown(event, index)}
              className={cn(
                "relative min-h-11 rounded-full px-6 text-[0.9375rem] font-semibold transition-colors duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                selected ? "text-ink" : "text-ink-soft hover:text-ink",
              )}
            >
              {selected ? (
                <span
                  aria-hidden="true"
                  className="absolute inset-0 rounded-full bg-surface shadow-soft"
                />
              ) : null}
              <span className="relative z-10">{platform.label}</span>
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <m.div
          key={active.id}
          role="tabpanel"
          id={`install-panel-${active.id}`}
          aria-labelledby={`install-tab-${active.id}`}
          initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
          transition={{ duration: reduceMotion ? 0.1 : 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col gap-6"
        >
          <div className="grid gap-4 md:grid-cols-3">
            {active.steps.map((step, index) => (
              <StepCard
                key={step.title}
                index={index + 1}
                title={step.title}
                text={step.text}
                illustration={<StepMiniIllustration variant={step.variant} />}
                className="h-full"
              />
            ))}
          </div>
          {active.note ? <p className="text-center text-[0.8125rem] text-ink-soft">{active.note}</p> : null}
        </m.div>
      </AnimatePresence>
    </div>
  );
}
