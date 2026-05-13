import { motion } from "framer-motion";
import { Quote } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { fadeInUp, staggerContainer } from "@/animations/variants";

const TESTIMONIALS = [
  {
    quote:
      "I used to lose 2-3 hours a week chasing case files across desktop folders and WhatsApp. Now my hearings, documents, and notes for every case live in one place.",
    name: "Adv. Hassan Raza",
    role: "Family Law Practitioner, Lahore",
    initials: "HR",
  },
  {
    quote:
      "The bilingual chatbot is the first one I've actually trusted. It cites the source, refuses to answer when it doesn't know, and works in Urdu — which my older clients prefer.",
    name: "Adv. Ayesha Malik",
    role: "Civil Lawyer, Karachi",
    initials: "AM",
  },
  {
    quote:
      "As a third-year LLB student, the practice simulator is the closest thing I've had to courtroom practice. The rubric feedback genuinely tells me where my arguments fall short.",
    name: "Bilal Ahmed",
    role: "LLB Student, Punjab University",
    initials: "BA",
  },
];

export default function Testimonials() {
  return (
    <Section className="relative">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-16"
        >
          <Badge variant="gold" className="mb-4">
            Voices from the field
          </Badge>
          <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5">
            Built with feedback from{" "}
            <span className="gold-text">real practitioners</span>.
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Designed iteratively with lawyers, clients, and law students at NUCES.
          </p>
        </motion.div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid gap-6 lg:grid-cols-3"
        >
          {TESTIMONIALS.map((t) => (
            <motion.div
              key={t.name}
              variants={fadeInUp}
              className="relative rounded-2xl border border-border/50 bg-card/40 p-8 backdrop-blur-sm"
            >
              <Quote className="absolute -top-3 -left-3 h-10 w-10 text-legal-gold/40" strokeWidth={1.5} />

              <p className="text-foreground/90 leading-relaxed mb-6 text-[15px]">
                "{t.quote}"
              </p>

              <div className="flex items-center gap-3 pt-4 border-t border-border/30">
                <Avatar>
                  <AvatarFallback className="bg-gold-gradient text-legal-navy font-semibold text-xs">
                    {t.initials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div className="text-sm font-semibold">{t.name}</div>
                  <div className="text-xs text-muted-foreground">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </Container>
    </Section>
  );
}
