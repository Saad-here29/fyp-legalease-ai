import { ArrowRight } from "lucide-react";
import Container from "@/components/layout/Container";
import AppButton from "@/components/ui/AppButton";
import ArchPattern from "@/components/common/ArchPattern";
import { ROUTES } from "@/constants";

// Single-section hero: one confident headline, one primary action, and an
// example answer in the same format the AI assistant actually uses.
export default function Hero() {
  return (
    <section className="relative pt-36 pb-24 overflow-hidden">
      <ArchPattern className="text-ink-panel opacity-[0.07]" />

      <Container className="relative">
        <div className="grid gap-16 lg:grid-cols-[1.15fr_1fr] items-center">
          <div>
            <p className="eyebrow mb-6">AI-powered · Made for Pakistan</p>

            <h1 className="type-display">The legal workspace for modern Pakistan.</h1>

            <p className="type-lead mt-7 max-w-xl">
              Case management, document analysis and statute-grounded legal
              research — for lawyers, clients and law students.
            </p>

            <div className="mt-10">
              <AppButton to={ROUTES.WELCOME} className="text-base py-3.5 px-8">
                Get started
                <ArrowRight className="h-4 w-4" />
              </AppButton>
            </div>

            <ul className="mt-12 pt-6 border-t border-hairline flex flex-wrap gap-x-8 gap-y-2 text-[15px] text-ink-muted">
              <li>English &amp; Urdu</li>
              <li>Answers cite the statute passage</li>
              <li>Role-based access</li>
            </ul>
          </div>

          <HeroVisual />
        </div>
      </Container>
    </section>
  );
}

/* Example answer in the assistant's real format: answer text, a metadata
   line, then numbered footnotes. The answer paraphrases the actual MFLO
   Section 9 passage in the statute library. */
function HeroVisual() {
  return (
    <div className="relative border border-hairline bg-paper p-7 w-full max-w-lg lg:ml-auto">
      <p className="type-meta mb-1.5">You</p>
      <p className="text-lg font-medium text-ink-text leading-snug">
        Can a wife claim maintenance through the Union Council?
      </p>

      <div className="mt-5 pt-5 border-t border-hairline-subtle">
        <p className="text-base text-ink-text leading-relaxed">
          Yes. Under <strong className="font-semibold">Section 9 of the Muslim Family Laws Ordinance, 1961</strong>,
          if a husband fails to maintain his wife adequately she may apply to the
          Chairman, who constitutes an Arbitration Council to fix the amount he
          must pay.<sup className="citation-marker">1</sup>
        </p>
        <p className="type-meta mt-4">1 statute · 4.8s</p>
        <ol className="mt-3 pt-3 border-t border-hairline-subtle">
          <li className="flex gap-3 text-sm">
            <span className="text-brick font-semibold w-4 text-right">1</span>
            <span className="text-ink-text font-medium">
              Muslim Family Laws Ordinance, 1961 — Section 9, Maintenance
            </span>
          </li>
        </ol>
      </div>
    </div>
  );
}
