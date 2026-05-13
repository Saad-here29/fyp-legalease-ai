import { motion } from "framer-motion";
import {
  Briefcase,
  MessageSquareText,
  FileText,
  Search,
  GraduationCap,
  PenLine,
  ScanLine,
  BellRing,
  LayoutDashboard,
} from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import FeatureCard from "@/components/common/FeatureCard";
import { Badge } from "@/components/ui/badge";
import { fadeInUp } from "@/animations/variants";

const MODULES = [
  {
    icon: Briefcase,
    title: "Case Management",
    description:
      "Full case lifecycle with state machine: Created → Assigned → In-Progress → Hearing → Closed. Timeline, hearings, deadlines, and audit-logged events.",
  },
  {
    icon: MessageSquareText,
    title: "AI Legal Chat",
    description:
      "Bilingual legal Q&A grounded in Pakistani statutes and judgments. Persistent chat history per case (last 50 exchanges).",
  },
  {
    icon: FileText,
    title: "Document Analysis",
    description:
      "Upload PDFs, DOCX, or text. AI summarises, identifies parties/jurisdiction/indemnity clauses, and flags missing terms against templates.",
  },
  {
    icon: Search,
    title: "AI Legal Research",
    description:
      "Natural-language search over the legal library with semantic ranking, court/year/type filters, and similar-case suggestions.",
  },
  {
    icon: ScanLine,
    title: "OCR Pipeline",
    description:
      "Tesseract-based extraction for scanned PDFs and images. ≥90% English accuracy, ≥80% on Urdu. Async via Celery.",
  },
  {
    icon: PenLine,
    title: "Contract Drafting",
    description:
      "Reusable templates (NDA, Employment, Service Agreement), AI clause suggestions, compliance checks, and version diff.",
  },
  {
    icon: GraduationCap,
    title: "Practice Simulator",
    description:
      "Interactive scenarios for law students with virtual clients/judges. Rubric-based feedback and progress tracking across sessions.",
  },
  {
    icon: BellRing,
    title: "Smart Notifications",
    description:
      "In-app alerts within 5s of hearing changes plus email reminders 24h before each hearing. Read state persists across reloads.",
  },
  {
    icon: LayoutDashboard,
    title: "Role-Specific Dashboards",
    description:
      "Lawyers manage cases, clients view updates, students learn — each role gets a tailored workspace with one-click access to AI tools.",
  },
];

export default function Features() {
  return (
    <Section id="features" className="relative">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-16"
        >
          <Badge variant="gold" className="mb-4">
            Modules
          </Badge>
          <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5">
            Nine modules. <span className="gold-text">One platform.</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Each module owns a distinct part of the legal workflow, but every
            piece talks to the same backend through one secure API.
          </p>
        </motion.div>

        <div id="modules" className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((m, i) => (
            <FeatureCard
              key={m.title}
              icon={m.icon}
              title={m.title}
              description={m.description}
              delay={(i % 3) * 0.1}
            />
          ))}
        </div>
      </Container>
    </Section>
  );
}
