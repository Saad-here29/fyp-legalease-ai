import { Link } from "react-router-dom";
import { Construction, ArrowLeft } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";

const DASHBOARD_FOR_ROLE = {
  [ROLES.LAWYER]: ROUTES.LAWYER_DASHBOARD,
  [ROLES.CLIENT]: ROUTES.CLIENT_DASHBOARD,
  [ROLES.STUDENT]: ROUTES.STUDENT_DASHBOARD,
};

/**
 * Generic placeholder for sidebar tabs whose module isn't built yet.
 * Keeps the user inside the app shell (sidebar + header stay visible)
 * instead of bouncing them to the public landing page.
 *
 * Use with: <ComingSoonPage title="Clients" description="..." />
 */
export default function ComingSoonPage({
  title = "Coming soon",
  description = "This module is under development and will ship in the next iteration.",
  eta,
}) {
  const { user } = useAuthStore();
  const homeRoute = DASHBOARD_FOR_ROLE[user?.role] || ROUTES.LANDING;

  return (
    <AppShell title={title} subtitle="In progress">
      <div className="max-w-xl">
        <Construction className="h-8 w-8 text-ink-muted mb-5" />
        <h2 className="font-editorial text-2xl text-ink-text">{title}</h2>
        <p className="text-sm text-ink-muted mt-1">
          {eta ? `Shipping in ${eta}` : "In progress"}
        </p>
        <p className="text-sm text-ink-muted mt-5 leading-relaxed max-w-md">
          {description}
        </p>

        <Link
          to={homeRoute}
          className="mt-8 inline-flex items-center gap-1.5 text-sm text-brick hover:underline underline-offset-2"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to dashboard
        </Link>
      </div>
    </AppShell>
  );
}
