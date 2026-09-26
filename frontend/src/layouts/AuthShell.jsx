import { Link } from "react-router-dom";
import { Check } from "lucide-react";
import { ArchOutlines } from "@/components/common/ArchPattern";
import Wordmark from "@/components/common/Wordmark";
import { ROUTES } from "@/constants";

// Shared shell for every public auth page (Login, Signup, Welcome, Forgot
// Password, OTP, Reset Password) — design system v1, per the Login mockup
// (docs/design_reference page 2): ink identity panel on the left with the
// outline arches, a Display headline, a short statement and check-marked
// points; the form on Paper on the right.
//
// Copy here must stay true to the product: the AI answers from Pakistani
// statute text only (no judgments), and the library is the federal
// Pakistan Code.
export default function AuthShell({ heroTitle, heroSubtitle, heroPoints = [], children }) {
  return (
    <div className="min-h-screen grid grid-cols-1 grid-rows-[auto_1fr] lg:grid-rows-1 lg:grid-cols-[43fr_57fr] bg-ds-paper font-ds-sans text-ds-text">
      {/* Left — identity panel */}
      <div className="relative bg-ds-ink text-ds-paper overflow-hidden flex flex-col px-6 py-6 sm:px-10 lg:px-[60px] lg:py-11">
        <ArchOutlines className="hidden lg:block text-ds-paper/[0.07]" />

        <Link to={ROUTES.LANDING} className="relative w-fit rounded-ds focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-paper" aria-label="LegalEase AI home">
          <Wordmark onInk />
        </Link>

        <div className="relative hidden lg:flex flex-1 flex-col justify-end pt-24">
          {heroTitle && (
            <h1 className="font-ds-serif font-medium text-[clamp(48px,4.8vw,72px)] leading-[1.06] tracking-tight text-ds-paper">
              {heroTitle}
            </h1>
          )}
          {heroSubtitle && <p className="mt-8 max-w-[480px] text-[18px] leading-[28px] text-ds-paper/80">{heroSubtitle}</p>}
          {heroPoints.length > 0 && (
            <ul className="mt-12 space-y-3">
              {heroPoints.map((p) => (
                <li key={p} className="flex items-start gap-3 text-[16px] leading-[24px] text-ds-paper/80">
                  <Check className="h-5 w-5 shrink-0 mt-0.5 text-[#8FC7A4]" strokeWidth={2} aria-hidden="true" />
                  {p}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Right — form panel */}
      <div className="flex items-center justify-center px-4 sm:px-10 py-12 lg:py-16">
        <div className="w-full max-w-[428px]">{children}</div>
      </div>
    </div>
  );
}
