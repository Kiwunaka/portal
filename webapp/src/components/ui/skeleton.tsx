import { cn } from "@/components/utils";

/** Shared shimmer sweep (pokrov-clear): a soft highlight glides across the
 * placeholder instead of a flat opacity pulse. The global reduced-motion
 * kill-switch freezes it into a calm static block. */
const SWEEP = "skeleton-sweep";

export function SkeletonLine({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("rounded-full bg-skeleton", SWEEP, className)} />;
}

export function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("rounded-card border border-line bg-surface", SWEEP, className)}
    />
  );
}

/** Wrap page-shaped skeletons: announces loading politely, blocks stray reads. */
export function SkeletonRegion({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div aria-busy="true" aria-live="polite" aria-label={label} className={cn("space-y-4", className)}>
      {children}
    </div>
  );
}
