import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  FileText,
  Search,
  MessageSquare,
  CalendarDays,
  Bell,
  GraduationCap,
  BookOpen,
  TrendingUp,
  FileSignature,
  ScanLine,
  User,
  LogOut,
} from "lucide-react";
import Logo from "@/components/common/Logo";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { cn } from "@/lib/utils";

const NAV_BY_ROLE = {
  [ROLES.LAWYER]: [
    { to: ROUTES.LAWYER_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.CASES, label: "Cases", icon: Briefcase },
    { to: "/lawyer/clients", label: "Clients", icon: Users },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.RESEARCH, label: "Legal Research", icon: Search },
    { to: ROUTES.CHATBOT, label: "AI Assistant", icon: MessageSquare },
    { to: ROUTES.CONTRACTS, label: "Contracts", icon: FileSignature },
    { to: "/lawyer/schedule", label: "Schedule", icon: CalendarDays },
  ],
  [ROLES.CLIENT]: [
    { to: ROUTES.CLIENT_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.CASES, label: "My Cases", icon: Briefcase },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.CHATBOT, label: "AI Legal Chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Legal Research", icon: Search },
    { to: "/client/upload", label: "Upload & OCR", icon: ScanLine },
    { to: ROUTES.NOTIFICATIONS, label: "Notifications", icon: Bell },
  ],
  [ROLES.STUDENT]: [
    { to: ROUTES.STUDENT_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.SIMULATOR, label: "Practice Simulator", icon: GraduationCap },
    { to: ROUTES.CHATBOT, label: "AI Chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Legal Research", icon: Search },
    { to: "/student/library", label: "Library", icon: BookOpen },
    { to: "/student/progress", label: "Progress", icon: TrendingUp },
  ],
};

const ROLE_LABELS = {
  [ROLES.LAWYER]: "Lawyer Workspace",
  [ROLES.CLIENT]: "Client Portal",
  [ROLES.STUDENT]: "Student Workspace",
};

export default function Sidebar() {
  const { user, clear } = useAuthStore();
  const role = user?.role ?? ROLES.CLIENT;
  const items = NAV_BY_ROLE[role] ?? [];

  return (
    <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-border/40 bg-card/40 backdrop-blur-xl">
      <div className="px-6 py-6 border-b border-border/40">
        <Logo size="md" />
        <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {ROLE_LABELS[role]}
        </p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        {items.map(({ to, label, icon: Icon }, i) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <NavLink
              to={to}
              end
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent/15 text-accent border border-accent/30"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/40"
                )
              }
            >
              <Icon className="h-4 w-4" strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          </motion.div>
        ))}
      </nav>

      <div className="border-t border-border/40 p-3 space-y-1">
        <NavLink
          to={ROUTES.PROFILE}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-accent/15 text-accent"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary/40"
            )
          }
        >
          <User className="h-4 w-4" />
          <span>Profile</span>
        </NavLink>
        <button
          onClick={clear}
          className="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
