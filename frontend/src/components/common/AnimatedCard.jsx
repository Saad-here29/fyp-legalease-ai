import { motion } from "framer-motion";
import { fadeInUp } from "@/animations/variants";
import { cn } from "@/lib/utils";

/**
 * Card with on-scroll fade-up + subtle hover lift. Wraps any content.
 */
export default function AnimatedCard({ className, children, delay = 0, ...props }) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-80px" }}
      transition={{ delay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:border-legal-gold/40 hover:shadow-2xl hover:shadow-legal-gold/10",
        className
      )}
      {...props}
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-legal-gold/5 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
