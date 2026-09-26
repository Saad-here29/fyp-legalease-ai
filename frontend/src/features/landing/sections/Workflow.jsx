import { FileStack, Search, ShieldCheck, Quote } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";

const STEPS = [
  {
    icon: FileStack,
    step: "01",
    title: "Ingest & chunk",
    description: "Pakistani statute text is split into indexed passages.",
  },
  {
    icon: Search,
    step: "02",
    title: "Embed & search",
    description: "Your question is matched against the passage index by meaning.",
  },
  {
    icon: ShieldCheck,
    step: "03",
    title: "Verify confidence",
    description: "Low-confidence matches trigger a refusal, not a guess.",
  },
  {
    icon: Quote,
    step: "04",
    title: "Answer & cite",
    description: "The answer ships with the exact passages it came from.",
  },
];

export default function Workflow() {
  return (
    <Section id="how-it-works" className="border-t border-hairline">
      <Container>
        <div className="max-w-2xl mb-16">
          <p className="text-sm text-ink-muted mb-3">How answers are grounded</p>
          <h2 className="font-editorial text-4xl text-ink-text">
            Every answer traces back to a real source.
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.step} className="pt-6 border-t border-hairline">
              <div className="flex items-center gap-3 mb-4">
                <s.icon className="h-5 w-5 text-ink-muted" strokeWidth={2} />
                <span className="text-xs text-ink-muted">Step {s.step}</span>
              </div>
              <h3 className="font-editorial text-xl text-ink-text mb-2">{s.title}</h3>
              <p className="text-sm text-ink-muted leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
