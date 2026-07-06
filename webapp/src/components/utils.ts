import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-canvas";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
