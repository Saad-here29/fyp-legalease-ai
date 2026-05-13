import { motion } from "framer-motion";
import { Gavel, Users, BookOpenCheck, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fadeInUp, staggerContainer } from "@/animations/variants";
import { ROUTES } from "@/constants";

const ROLES = [
  {
    icon: Gavel,
    role: "Lawyers",
    accent: "from-amber-500/30 to-orange-500/10",
    description:
      "Full case ownership with structured workflows. Assign clients, schedule hearings, upload documents, and use AI to draft, research, and review.",
    bullets: [
      "Create + manage 30-50 active cases",
      "AI-assisted contract drafting & review",
      "Semantic legal research with citations",
      "Hearing reminders 24h in advance",
    ],
  },
  {
    icon: Users,
    role: "Clients",
    accent: "from-blue-500/30 to-indigo-500/10",
    description:
      "A read-only portal that finally answers \"what's happening with my case?\". Track progress, view shared documents, and ask the AI assistant.",
    bullets: [
      "Real-time case timeline",
      "View documents shared by lawyer",
      "Ask legal questions in English or Urdu",
      "Hearing notifications",
    ],
  },
  {
    icon: BookOpenCheck,
    role: "Law Students",
    accent: "from-emerald-500/30 to-teal-500/10",
    description:
      "Practice handling cases before stepping into a real courtroom. Interactive simulator with virtual clients, AI-graded feedback, and progress tracking.",
    bullets: [
      "10+ scenarios across civil, criminal, commercial",
      "Virtual client and judge conversations",
      "Rubric-based feedback (accuracy, structure, clarity)",
      "Progress dashboard across sessions",
    ],
  },
];

export default function LegalServices() {
  return (
    <Section className="relative bg-card/20">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-16"
        >
          <Badge variant="gold" className="mb-4">
            Built for every role
          </Badge>
          <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5">
            One platform, <span className="gold-text">three workspaces</span>.
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Each user gets a dashboard, sidebar, and permission set that matches
            their role — secured end-to-end with JWT and RBAC.
          </p>
        </motion.div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid gap-6 lg:grid-cols-3"
        >
          {ROLES.map((r) => (
            <motion.div
              key={r.role}
              variants={fadeInUp}
              whileHover={{ y: -6, transition: { duration: 0.25 } }}
              className="group relative overflow-hidden rounded-2xl border border-border/50 bg-card/40 p-8 backdrop-blur-sm"
            >
              <div
                className={`absolute inset-x-0 top-0 h-32 bg-gradient-to-b ${r.accent} opacity-50 blur-2xl group-hover:opacity-80 transition-opacity`}
              />

              <div className="relative">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-gold-gradient shadow-lg shadow-legal-gold/20">
                  <r.icon className="h-7 w-7 text-legal-navy" strokeWidth={2.2} />
                </div>

                <h3 className="font-serif text-2xl font-bold mb-3">
                  For {r.role}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed mb-6">
                  {r.description}
                </p>

                <ul className="space-y-2.5 mb-6">
                  {r.bullets.map((b) => (
                    <li
                      key={b}
                      className="flex items-start gap-2.5 text-sm text-foreground/85"
                    >
                      <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-legal-gold" />
                      {b}
                    </li>
                  ))}
                </ul>

                <Button asChild variant="ghost" size="sm" className="px-0 hover:bg-transparent">
                  <Link to={ROUTES.WELCOME} className="gold-text font-semibold">
                    Start as a {r.role.replace(/s$/, "").toLowerCase()}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </Container>
    </Section>
  );
}
