import type { SimpleIcon } from "simple-icons";

/** Real service logo from simple-icons, rendered in the brand's official color. */
export function BrandIcon({ className, icon, size = 18 }: { className?: string; icon: SimpleIcon; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={`#${icon.hex}`}
      aria-hidden="true"
      className={className}
    >
      <path d={icon.path} />
    </svg>
  );
}
