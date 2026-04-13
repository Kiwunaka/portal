import RouteTransition from "@/components/route-transition";

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <RouteTransition>
      <div className="min-h-full">{children}</div>
    </RouteTransition>
  );
}
