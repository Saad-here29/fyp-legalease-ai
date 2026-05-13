import { motion } from "framer-motion";
import { UserCheck, FileUp, Sparkles, CheckCircle2 } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import { Badge } from "@/components/ui/badge";
import { fadeInUp, staggerContainer } from "@/animations/variants";

const STEPS = [
  {
    icon: UserCheck,
    step: "01",
    title: "Sign in by role",
    description:
      "Pick Lawyer, Client, or Student. JWT-secured with bcrypt-hashed passwords (cost ≥12) and refresh-token rotation.",
  },
  {
    icon: FileUp,
    step: "02",
    title: "Add a case or document",
    description:
      "Lawyers create cases and upload PDFs, DOCX, or scanned images. Files stream to blob storage with SHA-256 dedup.",
  },
  {
    icon: Sparkles,
    step: "03",
    title: "Let the AI assist",
    description:
      "Ask in English or Urdu, search the legal library, or analyse a contract. Every answer is grounded with citations.",
  },
  {
    icon: CheckCircle2,
    step: "04",
    title: "Stay in sync",
    description:
      "Clients see real-time case timelines. Hearing reminders go out 24h ahead. Every privileged action is audit-logged.",
  },
];

export default function Workflow() {
  return (
    <Section id="workflow" className="relative">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-16"
        >
          <Badge variant="gold" className="mb-4">
            How it works
          </Badge>
          <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5">
            From sign-in to verdict, <span className="gold-text">end to end</span>.
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Four simple steps. Built around how Pakistani lawyers, clients,
            and students actually work.
          </p>
        </motion.div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="relative"
        >
          {/* Connecting line on lg+ */}
          <div className="hidden lg:block absolute top-8 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-transparent via-legal-gold/40 to-transparent" />

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s) => (
              <motion.div
                key={s.step}
                variants={fadeInUp}
                className="relative"
              >
                <div className="relative z-10 mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-gold-gradient shadow-xl shadow-legal-gold/30">
                  <s.icon className="h-7 w-7 text-legal-navy" strokeWidth={2.2} />
                </div>

                <div className="text-center">
                  <div className="text-xs font-mono font-semibold text-legal-gold mb-2 tracking-widest">
                    STEP {s.step}
                  </div>
                  <h3 className="font-serif text-xl font-semibold mb-2">
                    {s.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {s.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </Container>
    </Section>
  );
}
