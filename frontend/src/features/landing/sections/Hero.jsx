import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, Sparkles, ShieldCheck } from "lucide-react";
import Container from "@/components/layout/Container";
import GradientBackground from "@/components/common/GradientBackground";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fadeInUp, staggerContainer } from "@/animations/variants";
import { ROUTES } from "@/constants";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-32 pb-20 overflow-hidden">
      <GradientBackground />

      <Container className="relative z-10">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid gap-16 lg:grid-cols-2 items-center"
        >
          <div className="space-y-8">
            <motion.div variants={fadeInUp}>
              <Badge variant="gold" className="text-xs px-4 py-1.5">
                <Sparkles className="h-3 w-3 mr-1.5" />
                AI-Powered · Made for Pakistan
              </Badge>
            </motion.div>

            <motion.h1
              variants={fadeInUp}
              className="font-serif text-5xl lg:text-7xl font-bold leading-[1.05] tracking-tight"
            >
              The legal workspace for{" "}
              <span className="gold-text">modern Pakistan</span>.
            </motion.h1>

            <motion.p
              variants={fadeInUp}
              className="text-lg lg:text-xl text-muted-foreground leading-relaxed max-w-xl"
            >
              Manage cases, analyse contracts, and answer legal questions in
              English or Urdu — all in one platform built for lawyers,
              clients, and law students.
            </motion.p>

            <motion.div variants={fadeInUp} className="flex flex-wrap gap-4">
              <Button asChild variant="gold" size="xl">
                <Link to={ROUTES.WELCOME}>
                  Get Started
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="glass" size="xl">
                <a href="#features">Explore Features</a>
              </Button>
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className="flex flex-wrap items-center gap-6 pt-6 border-t border-border/30"
            >
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ShieldCheck className="h-4 w-4 text-legal-gold" />
                JWT + RBAC Secured
              </div>
              <div className="text-sm text-muted-foreground">
                English &amp; Urdu support
              </div>
              <div className="text-sm text-muted-foreground">
                Citation-backed AI answers
              </div>
            </motion.div>
          </div>

          <motion.div variants={fadeInUp} className="relative">
            <HeroVisual />
          </motion.div>
        </motion.div>
      </Container>
    </section>
  );
}

/* Animated visual — a stylised AI assistant card with floating tags */
function HeroVisual() {
  const floatTransition = (delay = 0) => ({
    initial: { y: 0 },
    animate: { y: [0, -10, 0] },
    transition: { duration: 4, repeat: Infinity, ease: "easeInOut", delay },
  });

  return (
    <div className="relative w-full max-w-lg mx-auto aspect-square">
      {/* Glow ring */}
      <div className="absolute inset-0 rounded-full bg-gold-gradient opacity-20 blur-3xl" />

      {/* Main card */}
      <motion.div
        {...floatTransition(0)}
        className="absolute inset-0 m-auto h-[420px] w-[360px] glass-card p-6 rounded-3xl"
      >
        <div className="flex items-center gap-3 pb-4 border-b border-white/10">
          <div className="h-9 w-9 rounded-lg bg-gold-gradient flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-legal-navy" />
          </div>
          <div>
            <div className="text-sm font-semibold">LegalEase Assistant</div>
            <div className="text-xs text-muted-foreground">RAG · FAISS · GPT-4o</div>
          </div>
        </div>

        <div className="space-y-3 pt-5 text-sm">
          <div className="rounded-xl bg-secondary/40 p-3 text-foreground/80">
            What does Section 13 of the Family Courts Act say?
          </div>
          <div className="rounded-xl border border-legal-gold/30 bg-legal-gold/5 p-3 text-foreground/90 leading-relaxed">
            Section 13 governs interim orders during family suits.{" "}
            <span className="text-legal-gold underline">[Family Courts Act, §13]</span>{" "}
            The court may pass orders pertaining to maintenance...
            <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Sourced from 2 cited passages
            </div>
          </div>
        </div>
      </motion.div>

      {/* Floating tags */}
      <motion.div
        {...floatTransition(0.6)}
        className="absolute top-8 -left-4 glass-card px-3 py-2 rounded-xl text-xs font-medium"
      >
        ⚖️ 5,000+ Pakistani statutes
      </motion.div>
      <motion.div
        {...floatTransition(1.2)}
        className="absolute bottom-12 -right-4 glass-card px-3 py-2 rounded-xl text-xs font-medium"
      >
        📄 OCR · Urdu &amp; English
      </motion.div>
      <motion.div
        {...floatTransition(0.3)}
        className="absolute top-1/3 -right-8 glass-card px-3 py-2 rounded-xl text-xs font-medium"
      >
        🔒 RBAC Enforced
      </motion.div>
    </div>
  );
}
