"use client";

import { useState } from "react";

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
  const active = platforms.find((platform) => platform.id === activeId) ?? platforms[0];

  return (
    <div className="flex flex-col gap-8">
      <div
        role="tablist"
        aria-label="Платформа"
        className="mx-auto flex rounded-full border border-line bg-canvas-alt p-1"
      >
        {platforms.map((platform) => {
          const selected = platform.id === active.id;
          return (
            <button
              key={platform.id}
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`install-panel-${platform.id}`}
              id={`install-tab-${platform.id}`}
              onClick={() => setActiveId(platform.id)}
              className={cn(
                "min-h-11 rounded-full px-6 text-[0.9375rem] font-semibold transition-[background-color,color,box-shadow] duration-200 ease-(--ease-apple)",
                selected ? "bg-surface text-ink shadow-soft" : "text-ink-soft hover:text-ink",
              )}
            >
              {platform.label}
            </button>
          );
        })}
      </div>

      <div
        key={active.id}
        role="tabpanel"
        id={`install-panel-${active.id}`}
        aria-labelledby={`install-tab-${active.id}`}
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
        {active.note ? <p className="text-center text-[0.8125rem] text-ink-muted">{active.note}</p> : null}
      </div>
    </div>
  );
}
