import { useNavigate, Link } from "react-router-dom";
import { Gavel, Users, BookOpenCheck, ArrowRight } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { ROUTES, ROLES } from "@/constants";

const ROLE_OPTIONS = [
  {
    role: ROLES.LAWYER,
    icon: Gavel,
    title: "I'm a lawyer",
    description: "Manage cases, draft contracts, research law.",
  },
  {
    role: ROLES.CLIENT,
    icon: Users,
    title: "I'm a client",
    description: "Track my case progress and shared documents.",
  },
  {
    role: ROLES.STUDENT,
    icon: BookOpenCheck,
    title: "I'm a law student",
    description: "Practice scenarios and search the legal library.",
  },
];

export default function WelcomePage() {
  const navigate = useNavigate();

  const handleSelect = (role) => {
    navigate(`${ROUTES.SIGNUP}?role=${role}`);
  };

  return (
    <AuthShell
      heroTitle="Welcome."
      heroSubtitle="Choose how you'd like to use LegalEase AI."
    >
      <h2 className="font-editorial text-2xl text-ink-text mb-1">Get started</h2>
      <p className="text-sm text-ink-muted mb-6">
        Choose how you'd like to use the platform.
      </p>

      <div className="border-b border-hairline-subtle mb-6" />

      <div>
        {ROLE_OPTIONS.map((opt) => (
          <button
            key={opt.role}
            onClick={() => handleSelect(opt.role)}
            className="group w-full text-left py-4 px-2 -mx-2 border-b border-hairline-subtle last:border-0 flex items-center gap-4 hover:bg-hairline-subtle/40 transition-colors"
          >
            <opt.icon className="h-5 w-5 text-ink-muted shrink-0" strokeWidth={2} />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-ink-text">{opt.title}</div>
              <div className="text-xs text-ink-muted">{opt.description}</div>
            </div>
            <ArrowRight className="h-4 w-4 text-ink-muted shrink-0 group-hover:translate-x-0.5 transition-transform" />
          </button>
        ))}
      </div>

      <div className="mt-8 pt-6 border-t border-hairline-subtle text-center">
        <p className="text-sm text-ink-muted">
          Already have an account?{" "}
          <Link to={ROUTES.LOGIN} className="text-brick hover:underline underline-offset-2">
            Sign in
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
