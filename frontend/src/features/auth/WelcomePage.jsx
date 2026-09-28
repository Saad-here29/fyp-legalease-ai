import { useNavigate, Link } from "react-router-dom";
import { Gavel, Users, BookOpenCheck, ArrowRight } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { ROUTES, ROLES } from "@/constants";

// First step of creating an account: choose a role, then the Signup form
// (which reads it from ?role=). Every "Create an account" link leads here.
const ROLE_OPTIONS = [
  {
    role: ROLES.LAWYER,
    icon: Gavel,
    title: "I'm a lawyer",
    description: "Manage cases, analyse documents, draft contracts, research law.",
  },
  {
    role: ROLES.CLIENT,
    icon: Users,
    title: "I'm a client",
    description: "Follow your case and the documents shared on it.",
  },
  {
    role: ROLES.STUDENT,
    icon: BookOpenCheck,
    title: "I'm a law student",
    description: "Ask about statutes and search the statute library.",
  },
];

export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <AuthShell heroAlign="center" heroTitle="Welcome." heroSubtitle="Choose how you'd like to use LegalEase AI.">
      <p className="ds-eyebrow">Step 1 of 2</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Create an account
      </h1>
      <p className="ds-body text-ds-text-2 mt-2">Choose how you&apos;ll use LegalEase.</p>

      <ul className="mt-8 border-t-2 border-ds-ink">
        {ROLE_OPTIONS.map((opt) => (
          <li key={opt.role} className="border-b border-ds-rule">
            <button
              onClick={() => navigate(`${ROUTES.SIGNUP}?role=${opt.role}`)}
              className="group w-full text-left min-h-[72px] py-4 flex items-center gap-4 hover:bg-ds-sheet/70
                focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink rounded-ds-sm"
            >
              <opt.icon className="h-6 w-6 text-ds-text-2 shrink-0 ml-1" strokeWidth={1.8} aria-hidden="true" />
              <span className="flex-1 min-w-0">
                <span className="block font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text">{opt.title}</span>
                <span className="block ds-meta">{opt.description}</span>
              </span>
              <ArrowRight className="h-5 w-5 text-ds-text-2 shrink-0 mr-1 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>

      <p className="mt-8 text-center text-[16px] text-ds-text-2">
        Already have an account?{" "}
        <Link to={ROUTES.LOGIN} className="ds-link-seal">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
