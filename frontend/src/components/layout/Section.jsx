import { cn } from "@/lib/utils";

/**
 * Vertically padded page section. Generous spacing per the premium SaaS feel.
 */
export default function Section({ className, children, id, ...props }) {
  return (
    <section
      id={id}
      className={cn("relative w-full py-20 lg:py-28", className)}
      {...props}
    >
      {children}
    </section>
  );
}
