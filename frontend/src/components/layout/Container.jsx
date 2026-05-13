import { cn } from "@/lib/utils";

/**
 * Page-width container — caps content width and adds responsive horizontal
 * padding. Use as a top-level wrapper inside every section.
 */
export default function Container({ className, children, ...props }) {
  return (
    <div className={cn("mx-auto w-full max-w-7xl px-6 lg:px-8", className)} {...props}>
      {children}
    </div>
  );
}
