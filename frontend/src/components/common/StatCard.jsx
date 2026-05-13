import { motion } from "framer-motion";
import { fadeInUp } from "@/animations/variants";

/**
 * Stat highlight — large gold number, label, and optional supporting text.
 * Used in the landing page Stats section.
 */
export default function StatCard({ value, label, helper, delay = 0 }) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      transition={{ delay }}
      className="relative rounded-2xl border border-border/40 bg-card/40 p-8 backdrop-blur-sm"
    >
      <div className="text-5xl lg:text-6xl font-serif font-bold gold-text leading-none">
        {value}
      </div>
      <div className="mt-3 text-sm font-semibold uppercase tracking-wider text-foreground">
        {label}
      </div>
      {helper && (
        <p className="mt-2 text-sm text-muted-foreground">{helper}</p>
      )}
    </motion.div>
  );
}
