import { cn } from "@/components/utils";

export function SkeletonLine({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("rounded-full bg-skeleton motion-safe:animate-pulse", className)} />;
}

export function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("rounded-card border border-line bg-surface motion-safe:animate-pulse", className)}
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
