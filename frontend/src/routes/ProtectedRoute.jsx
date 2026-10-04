import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { ROUTES, dashboardRouteFor } from "@/constants";

/**
 * Wraps protected routes. Redirects to /login if the user is not authenticated,
 * and to the user's OWN dashboard if their role is not allowed for the route
 * (so e.g. a Client trying to hit /lawyer/dashboard is bounced to /client/dashboard,
 * not to the public landing page).
 *
 * Usage:
 *   <ProtectedRoute allowedRoles={[ROLES.LAWYER]}>
 *     <LawyerDashboard />
 *   </ProtectedRoute>
 */
export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  if (allowedRoles?.length && !allowedRoles.includes(user?.role)) {
    return <Navigate to={dashboardRouteFor(user?.role)} replace />;
  }

  return children;
}
