import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg)] dark:focus-visible:ring-emerald-300 dark:focus-visible:ring-offset-[var(--bg-dark)]";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
