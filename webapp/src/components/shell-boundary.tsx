"use client";

import { Badge, Button, type Tone } from "./cabinet/ui";
import { CabinetIcon } from "./cabinet/icon";
import {
  DialogShell,
  EmptyState,
  MetricCard,
  SectionHeader,
  Timeline,
} from "./shell-primitives";

type RecoveryAction = {
  label: string;
  href?: string;
  onClick?: () => void;
  external?: boolean;
};

type ShellBoundaryProps = {
  eyebrow: string;
  title: string;
  description: string;
  badgeLabel: string;
  badgeTone: Tone;
  primaryAction: RecoveryAction;
  secondaryAction: RecoveryAction;
  metrics: Array<{ label: string; value: string; hint: string; tone?: "emerald" | "amber" | "rose" | "slate" }>;
  steps: Array<{ title: string; description: string; tone?: Tone }>;
  icon: string;
};

function ActionButton({ action, primary }: { action: RecoveryAction; primary?: boolean }) {
  return (
    <Button
      variant={primary ? "primary" : "secondary"}
      href={action.href}
      target={action.external ? "_blank" : undefined}
      rel={action.external ? "noreferrer noopener" : undefined}
      onClick={action.onClick}
    >
      {action.label}
    </Button>
  );
}

export function ShellBoundary({
  eyebrow,
  title,
  description,
  badgeLabel,
  badgeTone,
  primaryAction,
  secondaryAction,
  metrics,
  steps,
  icon,
}: ShellBoundaryProps) {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <DialogShell eyebrow={eyebrow} actions={<Badge tone={badgeTone}>{badgeLabel}</Badge>} className="relative">
        <div className="grid gap-6 xl:grid-cols-[1.03fr_0.97fr]">
          <EmptyState
            icon={<CabinetIcon name={icon} className="h-8 w-8" />}
            title={title}
            description={description}
            actions={
              <>
                <ActionButton action={primaryAction} primary />
                <ActionButton action={secondaryAction} />
              </>
            }
            className="h-full justify-center px-5 py-8"
          />

          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              {metrics.map((metric) => (
                <MetricCard key={metric.label} label={metric.label} value={metric.value} hint={metric.hint} tone={metric.tone} />
              ))}
            </div>

            <div className="rounded-[1.5rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5">
              <SectionHeader
                eyebrow="recovery"
                title="Что делать дальше"
                description="Эти действия помогут вернуться в рабочую зону."
              />
              <Timeline
                className="mt-5"
                items={steps}
              />
            </div>
          </div>
        </div>
      </DialogShell>
    </main>
  );
}
