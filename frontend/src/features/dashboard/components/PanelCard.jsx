import { motion } from "framer-motion";
import { fadeInUp } from "@/animations/variants";
import { cn } from "@/lib/utils";

/**
 * Glass panel used for tables, lists, and grouped content on dashboards.
 */
export default function PanelCard({
  title,
  description,
  action,
  children,
  className,
  delay = 0,
}) {
  return (
    <motion.section
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      transition={{ delay }}
      className={cn(
        "rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm",
        className
      )}
    >
      {(title || action) && (
        <header className="flex items-start justify-between gap-4 px-5 pt-5">
          <div className="min-w-0">
            {title && (
              <h2 className="font-serif text-lg font-semibold tracking-tight">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-sm text-muted-foreground mt-0.5">
                {description}
              </p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className="p-5">{children}</div>
    </motion.section>
  );
}
