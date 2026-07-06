import { cn } from "@/components/utils";

type MeterTone = "ok" | "warning" | "danger";

const FILL_CLASS: Record<MeterTone, string> = {
  ok: "bg-progress-fill",
  warning: "bg-progress-warn",
  danger: "bg-progress-danger",
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
