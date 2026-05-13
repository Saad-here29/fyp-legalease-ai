import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import Hero from "./sections/Hero";
import Stats from "./sections/Stats";
import AICapabilities from "./sections/AICapabilities";
import Features from "./sections/Features";
import LegalServices from "./sections/LegalServices";
import Workflow from "./sections/Workflow";
import Testimonials from "./sections/Testimonials";
import CallToAction from "./sections/CallToAction";

/**
 * Public landing page composition. Sections are kept individually so they can
 * be reordered or A/B tested without touching the others.
 */
export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-background text-foreground overflow-x-hidden">
      <Navbar />
      <main>
        <Hero />
        <Stats />
        <AICapabilities />
        <Features />
        <LegalServices />
        <Workflow />
        <Testimonials />
        <CallToAction />
      </main>
      <Footer />
    </div>
  );
}
