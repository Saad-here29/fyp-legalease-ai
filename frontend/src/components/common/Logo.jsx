import { Scale } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * LegalEase AI brand mark for light/paper contexts (Navbar, Footer).
 * Flat — no gradient tile, no uppercase tracking.
 */
export default function Logo({ className, showWordmark = true, size = "md" }) {
  const sizes = {
    sm: { icon: "h-4 w-4", text: "text-base" },
    md: { icon: "h-5 w-5", text: "text-lg" },
    lg: { icon: "h-6 w-6", text: "text-xl" },
  };
  const s = sizes[size];

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Scale className={cn("text-ink-text", s.icon)} strokeWidth={2} />
      {showWordmark && (
        <span className={cn("font-editorial text-ink-text", s.text)}>LegalEase AI</span>
      )}
    </div>
  );
}
