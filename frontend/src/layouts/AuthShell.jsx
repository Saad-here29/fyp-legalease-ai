import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import ArchPattern from "@/components/common/ArchPattern";
import { ROUTES } from "@/constants";

// Shared shell for every public auth page (Login, Signup, Welcome, Forgot
// Password, OTP, Reset Password) — the two-pane ink-panel/paper split
// introduced on the Login page. Extracted here once several pages needed
// the identical treatment, so it isn't duplicated per page. Distinct from
// the old AuthLayout.jsx (dark navy/gold glassmorphism), which this
// replaces for every converted auth page.
//
// `showArch`: the faint architectural-arch background motif is spec'd for
// every auth page's dark panel (and the Landing hero, separately). Defaults
// on so every current and future AuthShell consumer matches automatically;
// pass `showArch={false}` for the rare page that shouldn't have it.
export default function AuthShell({ heroTitle, heroSubtitle, tagline, showArch = true, children }) {
  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      {/* Left — identity / hero panel */}
      <div className="relative bg-ink-panel text-paper flex flex-col px-8 py-10 md:px-14 md:py-14 overflow-hidden">
        {showArch && <ArchPattern className="text-paper opacity-[0.08]" />}

        <Link
          to={ROUTES.LANDING}
          className="relative z-10 inline-flex items-center gap-2 text-base font-medium text-paper/85 hover:text-paper transition-colors w-fit"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <div className="relative z-10 flex-1 flex flex-col justify-center max-w-sm">
          <div className="flex items-center gap-2.5 mb-10">
            <Scale className="h-5 w-5 text-paper/70" strokeWidth={2} />
            <span className="text-sm text-paper/70">LegalEase AI</span>
          </div>

          <h1 className="font-editorial text-4xl leading-tight mb-3">{heroTitle}</h1>
          {heroSubtitle && (
            <p className="text-sm text-paper/60 leading-relaxed">{heroSubtitle}</p>
          )}
        </div>

        <p className="relative z-10 text-xs text-paper/40">
          {tagline || "Pakistani law · case management & research"}
        </p>
      </div>

      {/* Right — form panel */}
      <div className="bg-paper flex items-center justify-center px-8 py-10 md:px-14 md:py-14">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
