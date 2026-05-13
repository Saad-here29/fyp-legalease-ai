import { motion } from "framer-motion";
import GradientBackground from "@/components/common/GradientBackground";
import Sidebar from "@/components/layout/Sidebar";
import DashboardHeader from "@/components/layout/DashboardHeader";
import { fadeIn } from "@/animations/variants";

/**
 * Shell for every authenticated, role-bound page. Renders the sidebar on the
 * left, a sticky header on top of the main pane, and animates the page body in.
 */
export default function DashboardLayout({ title, subtitle, children }) {
  return (
    <div className="relative min-h-screen flex">
      <GradientBackground />

      <Sidebar />

      <div className="relative z-10 flex-1 flex flex-col min-w-0">
        <DashboardHeader title={title} subtitle={subtitle} />

        <motion.main
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          className="flex-1 px-6 lg:px-10 py-6 lg:py-8 overflow-y-auto scrollbar-thin"
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
}
