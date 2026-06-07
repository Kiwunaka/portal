import Image from "next/image";
import type { CSSProperties } from "react";

type MarketingBrandLogoProps = {
  className?: string;
  height?: number;
  priority?: boolean;
  style?: CSSProperties;
  width?: number;
};

export function MarketingBrandLogo({
  className,
  height = 44,
  priority = false,
  style,
  width = 44,
}: MarketingBrandLogoProps) {
  return (
    <Image
      src="/pokrov-logo.svg"
      alt=""
      aria-hidden="true"
      className={className}
      width={width}
      height={height}
      priority={priority}
      style={style}
      unoptimized
    />
  );
}
