import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus,#20674f)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--atlas-canvas,#f7f3eb)]";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
