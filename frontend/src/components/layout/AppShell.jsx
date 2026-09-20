import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  FileText,
  Search,
  MessageSquare,
  CalendarDays,
  FileSignature,
  ScanLine,
  Bell,
  BookOpen,
  TrendingUp,
  GraduationCap,
  User,
  LogOut,
  Scale,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";

// Shared shell for every internal (authenticated) page — sidebar + header +
// main content area. Introduced while redesigning the app to the paper/ink
// editorial system (see docs/STYLE_GUIDE.md) so every page reuses exactly
// one sidebar/header implementation instead of each page carrying its own
// copy. Role-aware: nav items, workspace label, and dashboard route all
// follow the logged-in user's actual role.

const NAV_BY_ROLE = {
  [ROLES.LAWYER]: [
    { to: ROUTES.LAWYER_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.CASES, label: "Cases", icon: Briefcase },
    { to: "/lawyer/clients", label: "Clients", icon: Users },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.RESEARCH, label: "Legal research", icon: Search },
    { to: ROUTES.CHATBOT, label: "AI assistant", icon: MessageSquare },
    { to: ROUTES.CONTRACTS, label: "Contracts", icon: FileSignature },
    { to: "/lawyer/schedule", label: "Schedule", icon: CalendarDays },
  ],
  [ROLES.CLIENT]: [
    { to: ROUTES.CLIENT_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.CASES, label: "My cases", icon: Briefcase },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.CHATBOT, label: "AI legal chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Legal research", icon: Search },
    { to: "/client/upload", label: "Upload & OCR", icon: ScanLine },
    { to: ROUTES.NOTIFICATIONS, label: "Notifications", icon: Bell },
  ],
  [ROLES.STUDENT]: [
    { to: ROUTES.STUDENT_DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
    { to: ROUTES.SIMULATOR, label: "Practice simulator", icon: GraduationCap },
    { to: ROUTES.CHATBOT, label: "AI chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Legal research", icon: Search },
    { to: "/student/library", label: "Library", icon: BookOpen },
    { to: "/student/progress", label: "Progress", icon: TrendingUp },
  ],
};

const WORKSPACE_LABEL = {
  [ROLES.LAWYER]: "Lawyer workspace",
  [ROLES.CLIENT]: "Client portal",
  [ROLES.STUDENT]: "Student workspace",
};

export default function AppShell({ title, subtitle, headerActions, children }) {
  const { user, clear } = useAuthStore();
  const navItems = NAV_BY_ROLE[user?.role] || [];
  const initials =
    (user?.full_name || user?.email || "U")
      .split(/[\s@]/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="hidden lg:flex flex-col w-64 shrink-0 bg-ink-panel text-paper">
        <div className="px-6 py-6 border-b border-paper/10">
          <div className="flex items-center gap-2.5">
            <Scale className="h-5 w-5 text-paper/70" strokeWidth={2} />
            <span className="font-editorial text-lg">LegalEase AI</span>
          </div>
          <p className="mt-2 text-xs text-paper/50">
            {WORKSPACE_LABEL[user?.role] || "Workspace"}
          </p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-paper/10 text-paper"
                    : "text-paper/60 hover:text-paper hover:bg-paper/5"
                }`
              }
            >
              <Icon className="h-4 w-4" strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-paper/10 p-3 space-y-0.5">
          <NavLink
            to={ROUTES.PROFILE}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
                isActive
                  ? "bg-paper/10 text-paper"
                  : "text-paper/60 hover:text-paper hover:bg-paper/5"
              }`
            }
          >
            <User className="h-4 w-4" />
            <span>Profile</span>
          </NavLink>
          <button
            onClick={clear}
            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-paper/60 hover:text-paper hover:bg-paper/5 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="flex items-center justify-between gap-4 px-6 lg:px-10 py-6 border-b border-hairline">
          <div className="min-w-0">
            {title && (
              <h1 className="font-editorial text-2xl lg:text-3xl text-ink-text truncate">
                {title}
              </h1>
            )}
            {subtitle && <p className="text-sm text-ink-muted mt-1">{subtitle}</p>}
          </div>

          <div className="flex items-center gap-5 shrink-0">
            {headerActions}
            <button
              className="relative text-ink-muted hover:text-ink-text transition-colors"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-status-pending" />
            </button>
            <div className="flex items-center gap-3 pl-5 border-l border-hairline">
              <span className="hidden sm:block text-sm text-ink-text">
                {user?.full_name || user?.email || "Guest"}
              </span>
              <div className="h-9 w-9 rounded-full bg-ink-panel text-paper text-xs flex items-center justify-center shrink-0">
                {initials}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 px-6 lg:px-10 py-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
