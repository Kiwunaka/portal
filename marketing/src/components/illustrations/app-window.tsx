import Image from "next/image";

import { cn } from "../utils";

export function AppWindowIllustration({ className }: { className?: string }) {
  return (
    <figure
      className={cn(
        "m-0 w-full max-w-[660px] overflow-hidden rounded-[1.35rem] border border-line bg-surface p-1.5 shadow-strong",
        className,
      )}
    >
      <Image
        src="/app-screens/windows-home-1.0.6.png"
        alt="Реальное окно приложения POKROV VPN на Windows"
        width={1600}
        height={900}
        sizes="(min-width: 1024px) 660px, 92vw"
        className="h-auto w-full rounded-[1rem]"
      />
    </figure>
  );
}
