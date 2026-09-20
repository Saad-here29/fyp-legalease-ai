import { ArrowRight, ShieldCheck } from "lucide-react";
import Container from "@/components/layout/Container";
import AppButton from "@/components/ui/AppButton";
import ArchPattern from "@/components/common/ArchPattern";
import { ROUTES } from "@/constants";

// Single-section hero (headline, subheadline, CTA together on one paper
// background) with the arch-silhouette motif as a faint texture behind the
// whole section — not a two-panel split like AuthShell.
export default function Hero() {
  return (
    <section className="relative pt-36 pb-20 overflow-hidden">
      <ArchPattern className="text-ink-panel opacity-[0.07]" />

      <Container className="relative">
        <div className="grid gap-16 lg:grid-cols-2 items-center">
          <div>
            <p className="text-sm text-ink-muted mb-4">AI-powered · Made for Pakistan</p>

            <h1 className="font-editorial text-5xl lg:text-6xl leading-[1.1] text-ink-text">
              The legal workspace for modern Pakistan.
            </h1>

            <p className="mt-6 text-lg text-ink-muted leading-relaxed max-w-xl">
              AI-powered case management and legal research for Pakistani law.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-6">
              <AppButton to={ROUTES.WELCOME}>
                Get started
                <ArrowRight className="h-4 w-4" />
              </AppButton>
              <a href="#features" className="text-sm text-brick hover:underline underline-offset-2">
                Explore features
              </a>
            </div>

            <div className="mt-10 pt-6 border-t border-hairline flex flex-wrap items-center gap-6 text-sm text-ink-muted">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" />
                JWT + RBAC secured
              </div>
              <div>English &amp; Urdu support</div>
              <div>Citation-backed AI answers</div>
            </div>
          </div>

          <HeroVisual />
        </div>
      </Container>
    </section>
  );
}

/* Example chat panel — flat, hairline-bordered, no glow/glass/floating tags */
function HeroVisual() {
  return (
    <div className="relative border border-hairline p-6 max-w-md ml-auto w-full bg-paper">
      <div className="flex items-center gap-3 pb-4 border-b border-hairline-subtle">
        <div className="h-8 w-8 flex items-center justify-center border border-hairline">
          <span className="text-xs text-ink-text">AI</span>
        </div>
        <div>
          <div className="text-sm font-medium text-ink-text">LegalEase assistant</div>
          <div className="text-xs text-ink-muted">RAG · FAISS · Llama-3.3</div>
        </div>
      </div>

      <div className="pt-4 text-sm space-y-3">
        <p className="text-ink-muted">What does Section 13 of the Family Courts Act say?</p>
        <p className="text-ink-text leading-relaxed">
          Section 13 governs interim orders during family suits.
          <sup className="citation-marker">1</sup>
        </p>
        <ol className="text-xs text-ink-muted list-decimal list-inside pt-2 border-t border-hairline-subtle">
          <li>Family Courts Act 1964, §13</li>
        </ol>
      </div>
    </div>
  );
}
