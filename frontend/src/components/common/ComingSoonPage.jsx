import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Construction, ArrowLeft } from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";

const DASHBOARD_FOR_ROLE = {
  [ROLES.LAWYER]: ROUTES.LAWYER_DASHBOARD,
  [ROLES.CLIENT]: ROUTES.CLIENT_DASHBOARD,
  [ROLES.STUDENT]: ROUTES.STUDENT_DASHBOARD,
};

/**
 * Generic placeholder for sidebar tabs whose module isn't built yet.
 * Keeps the user inside the dashboard shell (sidebar + header stay visible)
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
    <DashboardLayout title={title} subtitle="In progress">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto"
      >
        <div className="rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm p-10 text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gold-gradient mb-5">
            <Construction className="h-8 w-8 text-legal-navy" />
          </div>
          <h2 className="font-serif text-3xl font-bold gold-text">{title}</h2>
          <Badge variant="gold" className="mt-3">
            {eta ? `Shipping in ${eta}` : "In Progress"}
          </Badge>
          <p className="text-sm text-muted-foreground mt-5 max-w-md mx-auto leading-relaxed">
            {description}
          </p>

          <div className="mt-8 flex items-center justify-center gap-3">
            <Button asChild variant="outline">
              <Link to={homeRoute}>
                <ArrowLeft className="h-4 w-4" />
                Back to dashboard
              </Link>
            </Button>
          </div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
