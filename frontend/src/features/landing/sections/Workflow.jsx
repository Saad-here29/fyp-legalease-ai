import { FileStack, Search, ShieldCheck, Quote, X } from "lucide-react";
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

// Each statement describes a behaviour the system enforces in code:
// no judgments in the index + case citations stripped (citation_check.py),
// ungrounded section numbers flagged "(unverified)", and the similarity
// threshold refusal for out-of-scope questions.
const NOT = [
  { title: "Not answers from case law we don't have", detail: "The library is statute text only; any case citation the model produces is removed." },
  { title: "Not section numbers it can't show you", detail: "A section missing from the retrieved passages is marked “unverified”." },
  { title: "Not guesses outside Pakistani law", detail: "Questions with no confident match in the library are refused." },
];

export default function Workflow() {
  return (
    <Section id="how-it-works" className="border-t border-hairline">
      <Container>
        <div className="max-w-2xl mb-16">
          <p className="eyebrow mb-4">How the AI assistant answers</p>
          <h2 className="type-section">Every answer traces back to a real source.</h2>
        </div>

        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.step} className="pt-6 border-t-2 border-ink-text">
              <div className="flex items-center gap-3 mb-5">
                <span className="text-sm font-semibold text-brick tabular-nums">{s.step}</span>
                <s.icon className="h-5 w-5 text-ink-muted" strokeWidth={2} />
              </div>
              <h3 className="font-editorial text-2xl text-ink-text mb-3">{s.title}</h3>
              <p className="text-base text-ink-muted leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>

        <ul className="mt-20 grid gap-8 md:grid-cols-3 border-t border-hairline pt-10">
          {NOT.map((n) => (
            <li key={n.title} className="flex gap-3">
              <X className="h-5 w-5 text-brick shrink-0 mt-0.5" strokeWidth={2.5} aria-hidden />
              <div>
                <p className="text-base font-semibold text-ink-text">{n.title}</p>
                <p className="text-[15px] text-ink-muted mt-1 leading-relaxed">{n.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </Container>
    </Section>
  );
}
