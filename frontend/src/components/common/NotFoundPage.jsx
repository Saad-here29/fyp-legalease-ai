import { Link } from "react-router-dom";
import Wordmark from "./Wordmark";
import { useAuthStore } from "@/store/authStore";
import { ROUTES, dashboardRouteFor } from "@/constants";

// Any unknown address, design system v1. Replaces the eight "coming soon"
// placeholder routes and the old catch-all, which silently sent every
// mistyped URL to the landing page.

export default function NotFoundPage() {
  const { isAuthenticated, user } = useAuthStore();
  const home = isAuthenticated ? dashboardRouteFor(user?.role) : ROUTES.LANDING;

  return (
    <main className="min-h-screen bg-ds-paper text-ds-text flex flex-col">
      <header className="px-4 sm:px-10 py-6">
        <Link to={ROUTES.LANDING} aria-label="LegalEase home" className="inline-flex rounded-ds-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink">
          <Wordmark />
        </Link>
      </header>
      <section className="flex-1 flex items-center px-4 sm:px-10 pb-24">
        <div className="max-w-[560px]">
          <p className="ds-eyebrow">Error 404</p>
          <h1 className="ds-h1 mt-3">Page not found.</h1>
          <p className="ds-body text-ds-text-2 mt-4">
            This page doesn&apos;t exist, or it has moved. Check the address, or carry on from{" "}
            {isAuthenticated ? "your dashboard" : "the home page"}.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={home} className="ds-btn-primary">
              {isAuthenticated ? "Go to your dashboard" : "Go to the home page"}
            </Link>
            {!isAuthenticated && (
              <Link to={ROUTES.LOGIN} className="ds-btn-secondary">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
