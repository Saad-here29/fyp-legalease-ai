import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Gavel, Users, BookOpenCheck, ArrowRight } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import { fadeInUp, staggerContainer } from "@/animations/variants";
import { ROUTES, ROLES } from "@/constants";

const ROLE_OPTIONS = [
  {
    role: ROLES.LAWYER,
    icon: Gavel,
    title: "I'm a Lawyer",
    description: "Manage cases, draft contracts, research law.",
  },
  {
    role: ROLES.CLIENT,
    icon: Users,
    title: "I'm a Client",
    description: "Track my case progress and shared documents.",
  },
  {
    role: ROLES.STUDENT,
    icon: BookOpenCheck,
    title: "I'm a Law Student",
    description: "Practice scenarios and search the legal library.",
  },
];

export default function WelcomePage() {
  const navigate = useNavigate();

  const handleSelect = (role) => {
    navigate(`${ROUTES.SIGNUP}?role=${role}`);
  };

  return (
    <AuthLayout
      title="Welcome to LegalEase AI"
      subtitle="Choose how you'd like to use the platform."
      footer={
        <>
          Already have an account?{" "}
          <Link to={ROUTES.LOGIN} className="text-legal-gold hover:underline font-medium">
            Sign in
          </Link>
        </>
      }
    >
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-3"
      >
        {ROLE_OPTIONS.map((opt) => (
          <motion.button
            key={opt.role}
            variants={fadeInUp}
            onClick={() => handleSelect(opt.role)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.99 }}
            className="group w-full text-left p-4 rounded-xl border border-border/50 bg-secondary/30 hover:border-legal-gold/50 hover:bg-legal-gold/5 transition-all flex items-center gap-4"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold-gradient shadow-lg shadow-legal-gold/20 shrink-0">
              <opt.icon className="h-6 w-6 text-legal-navy" strokeWidth={2.2} />
            </div>
            <div className="flex-1">
              <div className="font-semibold text-foreground">{opt.title}</div>
              <div className="text-xs text-muted-foreground">{opt.description}</div>
            </div>
            <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-legal-gold group-hover:translate-x-1 transition-all" />
          </motion.button>
        ))}
      </motion.div>
    </AuthLayout>
  );
}
