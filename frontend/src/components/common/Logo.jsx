import { Scale } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * LegalEase AI brand mark — scales icon (justice) inside a gold gradient
 * tile, paired with serif wordmark.
 */
export default function Logo({ className, showWordmark = true, size = "md" }) {
  const sizes = {
    sm: { tile: "h-8 w-8", icon: "h-4 w-4", text: "text-base" },
    md: { tile: "h-10 w-10", icon: "h-5 w-5", text: "text-lg" },
    lg: { tile: "h-14 w-14", icon: "h-7 w-7", text: "text-2xl" },
  };
  const s = sizes[size];

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "flex items-center justify-center rounded-xl bg-gold-gradient shadow-lg shadow-legal-gold/20",
          s.tile
        )}
      >
        <Scale className={cn("text-legal-navy", s.icon)} strokeWidth={2.5} />
      </div>
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <span className={cn("font-serif font-bold tracking-tight gold-text", s.text)}>
            LegalEase
          </span>
          <span className="text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            AI · Pakistan
          </span>
        </div>
      )}
    </div>
  );
}
