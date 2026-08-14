import Image from "next/image";

import { cn } from "../utils";

export type AppPhoneVariant = "connect" | "locations" | "account";

const SCREENS: Record<
  AppPhoneVariant,
  { alt: string; src: string }
> = {
  connect: {
    alt: "Реальный главный экран POKROV VPN 1.0.6 на Android",
    src: "/app-screens/android-home-1.0.6.png",
  },
  locations: {
    alt: "Реальный экран локаций POKROV VPN 1.0.6 на Android",
    src: "/app-screens/android-locations-1.0.6.png",
  },
  account: {
    alt: "Реальный экран профиля POKROV VPN 1.0.6 на Android",
    src: "/app-screens/android-profile-1.0.6.png",
  },
};

export function AppPhoneIllustration({
  className,
  variant = "connect",
}: {
  className?: string;
  variant?: AppPhoneVariant;
}) {
  const screen = SCREENS[variant];
  return (
    <figure
      className={cn(
        "m-0 w-[280px] overflow-hidden rounded-[2rem] border border-line bg-surface p-1.5 shadow-strong sm:w-[300px]",
        className,
      )}
    >
      <Image
        src={screen.src}
        alt={screen.alt}
        width={1224}
        height={2628}
        sizes="(min-width: 640px) 300px, 280px"
        className="h-auto w-full rounded-[1.65rem]"
        priority={variant === "connect"}
      />
    </figure>
  );
}
