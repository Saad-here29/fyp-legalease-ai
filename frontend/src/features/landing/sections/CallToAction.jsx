import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import { Button } from "@/components/ui/button";
import { fadeInUp } from "@/animations/variants";
import { ROUTES } from "@/constants";

export default function CallToAction() {
  return (
    <Section className="relative">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="relative overflow-hidden rounded-3xl border border-legal-gold/30 bg-gradient-to-br from-legal-navy via-legal-ink to-legal-navy p-12 lg:p-16 text-center"
        >
          {/* Decorative blobs */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-legal-gold/20 blur-3xl" />
          <div className="absolute -bottom-32 -right-32 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />

          <div className="relative">
            <div className="inline-flex items-center gap-2 rounded-full border border-legal-gold/30 bg-legal-gold/10 px-4 py-1.5 text-xs font-medium text-legal-gold mb-6">
              <Sparkles className="h-3 w-3" />
              FYP-1 · Demo-ready · May 2026
            </div>

            <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5 max-w-2xl mx-auto">
              Ready to see <span className="gold-text">LegalEase AI</span> in action?
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-xl mx-auto mb-10">
              Sign in as a lawyer, client, or law student and explore the
              entire workflow — from case creation to AI-powered legal research.
            </p>

            <div className="flex flex-wrap justify-center gap-4">
              <Button asChild variant="gold" size="xl">
                <Link to={ROUTES.WELCOME}>
                  Get Started
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="glass" size="xl">
                <Link to={ROUTES.LOGIN}>I already have an account</Link>
              </Button>
            </div>
          </div>
        </motion.div>
      </Container>
    </Section>
  );
}
