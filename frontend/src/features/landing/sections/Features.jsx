import { Briefcase, FileText, GraduationCap } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import FeatureCard from "@/components/common/FeatureCard";

const MODULES = [
  {
    icon: Briefcase,
    title: "Case management",
    description: "Track every case from filing to hearing in one timeline.",
  },
  {
    icon: FileText,
    title: "Document analysis",
    description: "Upload a document and get OCR text plus an AI summary.",
  },
  {
    icon: GraduationCap,
    title: "Practice simulator",
    description: "Students rehearse arguments against an AI judge.",
  },
];

export default function Features() {
  return (
    <Section id="features" className="border-t border-hairline">
      <Container>
        <div className="max-w-2xl mb-16">
          <p className="eyebrow mb-4">Modules</p>
          <h2 className="type-section">
            Built for how Pakistani legal work actually happens.
          </h2>
        </div>

        <div className="grid gap-x-8 gap-y-10 md:grid-cols-3">
          {MODULES.map((m) => (
            <FeatureCard key={m.title} icon={m.icon} title={m.title} description={m.description} />
          ))}
        </div>
      </Container>
    </Section>
  );
}
