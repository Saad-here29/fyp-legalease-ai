import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import Logo from "@/components/common/Logo";
import GradientBackground from "@/components/common/GradientBackground";
import { fadeInUp } from "@/animations/variants";
import { ROUTES } from "@/constants";

/**
 * Wrapper for all auth pages — shared dark hero, brand mark, and a glass card
 * that hosts the page-specific form.
 */
export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-6 py-12 overflow-hidden">
      <GradientBackground />

      <div className="relative z-10 w-full max-w-md">
        <Link
          to={ROUTES.LANDING}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <div className="flex justify-center">
            <Logo size="lg" />
          </div>

          <div className="text-center space-y-2">
            <h1 className="font-serif text-3xl font-bold tracking-tight">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-muted-foreground">{subtitle}</p>
            )}
          </div>

          <div className="glass-card p-8 space-y-6">{children}</div>

          {footer && (
            <p className="text-center text-sm text-muted-foreground">{footer}</p>
          )}
        </motion.div>
      </div>
    </div>
  );
}
