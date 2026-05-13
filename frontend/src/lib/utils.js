import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges class names using clsx + tailwind-merge.
 * Required by ShadCN component conventions.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
