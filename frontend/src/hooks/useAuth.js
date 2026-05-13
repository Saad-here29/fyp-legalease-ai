import { useAuthStore } from "@/store/authStore";

/**
 * Convenience hook for components that only need read access to the
 * authenticated user. Components that need to mutate the session should
 * call useAuthStore directly.
 */
export function useAuth() {
  const { user, isAuthenticated, hasRole } = useAuthStore();
  return { user, isAuthenticated, hasRole };
}
