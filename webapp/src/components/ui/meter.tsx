import { cn } from "@/components/utils";

type MeterTone = "ok" | "warning" | "danger";

// component.progress fills can be gradients, so they must land on the
// `background` shorthand - Tailwind `bg-*` compiles to background-color,
// which silently drops gradient values.
const FILL_CLASS: Record<MeterTone, string> = {
  ok: "[background:var(--pokrov-progress-fill)]",
  warning: "[background:var(--pokrov-progress-warning-fill)]",
  danger: "[background:var(--pokrov-progress-danger-fill)]",
};

export function Meter({
  value,
  max,
  tone = "ok",
  label,
  className,
}: {
  value: number;
  max: number;
  tone?: MeterTone;
  label: string;
  className?: string;
}) {
  const safeMax = Math.max(1, max);
  const ratio = Math.min(1, Math.max(0, value / safeMax));
  return (
    <div
      role="meter"
      aria-valuemin={0}
      aria-valuemax={safeMax}
      aria-valuenow={Math.max(0, Math.min(safeMax, value))}
      aria-label={label}
      className={cn("h-2 overflow-hidden rounded-full bg-progress-track", className)}
    >
      <div
        className={cn("h-full rounded-full transition-[width] duration-300 ease-apple motion-reduce:transition-none", FILL_CLASS[tone])}
        style={{ width: `${ratio * 100}%` }}
      />
    </div>
  );
}
