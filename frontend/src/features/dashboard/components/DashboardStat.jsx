import { motion } from "framer-motion";
import { fadeInUp } from "@/animations/variants";
import { cn } from "@/lib/utils";

/**
 * Compact stat tile for dashboard hero rows. Trend is optional.
 * trend > 0 renders as positive, < 0 as negative.
 */
export default function DashboardStat({
  label,
  value,
  helper,
  trend,
  icon: Icon,
  delay = 0,
}) {
  const trendColor =
    trend == null
      ? "text-muted-foreground"
      : trend >= 0
      ? "text-emerald-400"
      : "text-rose-400";

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      transition={{ delay }}
      className="relative rounded-xl border border-border/40 bg-card/50 p-5 backdrop-blur-sm hover:border-accent/40 transition-colors"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        {Icon && (
          <div className="h-8 w-8 rounded-lg bg-accent/15 text-accent flex items-center justify-center">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      <div className="mt-3 text-3xl font-serif font-bold gold-text leading-none">
        {value}
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs">
        {trend != null && (
          <span className={cn("font-semibold", trendColor)}>
            {trend > 0 ? "+" : ""}
            {trend}%
          </span>
        )}
        {helper && <span className="text-muted-foreground">{helper}</span>}
      </div>
    </motion.div>
  );
}
