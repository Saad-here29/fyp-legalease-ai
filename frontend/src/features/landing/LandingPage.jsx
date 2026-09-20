import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import Hero from "./sections/Hero";
import Stats from "./sections/Stats";
import Workflow from "./sections/Workflow";
import Features from "./sections/Features";
import CallToAction from "./sections/CallToAction";

/**
 * Public landing page. Six sections per the design system spec: nav, hero
 * (with arch background), stats strip, "how answers are grounded" pipeline
 * (Workflow.jsx), 3-column feature grid (Features.jsx), final CTA.
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-paper text-ink-text">
      <Navbar />
      <main>
        <Hero />
        <Stats />
        <Workflow />
        <Features />
        <CallToAction />
      </main>
      <Footer />
    </div>
  );
}
