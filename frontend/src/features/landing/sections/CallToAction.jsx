import { ArrowRight } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import AppButton from "@/components/ui/AppButton";
import ArchPattern from "@/components/common/ArchPattern";
import { ROUTES } from "@/constants";

// Slightly lighter than the standard ink-panel (#1E2E28) so this card reads
// as a deliberate step up in tone against the paper section around it,
// rather than reusing the exact sidebar/hero green everywhere.
const CTA_GREEN = "#26382F";

export default function CallToAction() {
  return (
    <Section className="border-t border-hairline">
      <Container>
        <div
          className="relative overflow-hidden max-w-2xl mx-auto text-center text-paper p-12 lg:p-16"
          style={{ backgroundColor: CTA_GREEN }}
        >
          <ArchPattern className="text-paper opacity-[0.08]" />

          <div className="relative z-10">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-paper/60 mb-5">FYP-1 · Demo-ready</p>

            <h2 className="font-editorial text-4xl lg:text-5xl tracking-tight mb-5">
              See LegalEase AI in action.
            </h2>
            <p className="text-lg lg:text-xl text-paper/75 leading-relaxed mb-10">
              Sign in as a lawyer, client, or student to explore the workflow.
            </p>

            <div className="flex flex-wrap justify-center gap-6">
              <AppButton to={ROUTES.WELCOME} variant="inverted">
                Get started
                <ArrowRight className="h-4 w-4" />
              </AppButton>
              <AppButton to={ROUTES.LOGIN} variant="inverted-secondary">
                I already have an account
              </AppButton>
            </div>
          </div>
        </div>
      </Container>
    </Section>
  );
}
