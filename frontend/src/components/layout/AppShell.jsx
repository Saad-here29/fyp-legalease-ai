import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Home,
  Folder,
  MessageSquare,
  Search,
  FileText,
  PenLine,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/features/auth/api";
import { ROLES, ROUTES } from "@/constants";
import Wordmark from "@/components/common/Wordmark";

// Shared shell for every internal (authenticated) page — design system v1
// (docs/STYLE_GUIDE.md; sidebar per docs/design_reference page 7). The shell
// is only the ink sidebar; each page's title, meta line and its one primary
// action sit at the top of the content column, as in the Cases mockup.
//
// Nav lists only modules that exist. Placeholder routes (clients, schedule,
// notifications, library, progress, practice simulator, profile) stay
// routable but are not linked — no UI for features that aren't built.

const NAV_BY_ROLE = {
  [ROLES.LAWYER]: [
    { to: ROUTES.LAWYER_DASHBOARD, label: "Dashboard", icon: Home },
    { to: ROUTES.CASES, label: "Cases", icon: Folder },
    { to: ROUTES.CHATBOT, label: "AI Chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Research", icon: Search },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.CONTRACTS, label: "Contracts", icon: PenLine },
  ],
  [ROLES.CLIENT]: [
    { to: ROUTES.CLIENT_DASHBOARD, label: "Dashboard", icon: Home },
    { to: ROUTES.CASES, label: "My cases", icon: Folder },
    { to: ROUTES.CHATBOT, label: "AI Chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Research", icon: Search },
    { to: ROUTES.DOCUMENTS, label: "Documents", icon: FileText },
    { to: ROUTES.CONTRACTS, label: "Contracts", icon: PenLine },
  ],
  [ROLES.STUDENT]: [
    { to: ROUTES.STUDENT_DASHBOARD, label: "Dashboard", icon: Home },
    { to: ROUTES.CHATBOT, label: "AI Chat", icon: MessageSquare },
    { to: ROUTES.RESEARCH, label: "Research", icon: Search },
  ],
};

const SECTION_LABEL = {
  [ROLES.LAWYER]: "Practice",
  [ROLES.CLIENT]: "Your matters",
  [ROLES.STUDENT]: "Study",
};

const ROLE_LABEL = {
  [ROLES.LAWYER]: "Lawyer",
  [ROLES.CLIENT]: "Client",
  [ROLES.STUDENT]: "Law student",
};

// Two nested pointed arches, outline only — the sidebar's foot (page 7).
function SidebarArches() {
  const arch = (cx, w) =>
    `M${cx - w} 300V150C${cx - w} 95 ${cx - w * 0.45} 45 ${cx} 20C${cx + w * 0.45} 45 ${cx + w} 95 ${cx + w} 150V300`;
  return (
    <svg
      className="absolute bottom-0 left-0 w-full h-[300px] pointer-events-none text-ds-paper/10"
      viewBox="0 0 256 300"
      preserveAspectRatio="xMinYMax slice"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      aria-hidden="true"
    >
      <path d={arch(58, 84)} />
      <path d={arch(58, 50)} transform="translate(0 40)" />
      <path d={arch(236, 84)} />
    </svg>
  );
}

function Sidebar({ user, onNavigate, onSignOut }) {
  const navItems = NAV_BY_ROLE[user?.role] || [];
  const initials =
    (user?.full_name || user?.email || "U")
      .split(/[\s@]/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  return (
    <div className="relative h-full flex flex-col bg-ds-ink text-ds-paper font-ds-sans overflow-hidden">
      <SidebarArches />

      <div className="relative px-6 pt-7 pb-8">
        <Wordmark onInk />
      </div>

      <nav className="relative flex-1 px-3 overflow-y-auto" aria-label="Main">
        <p className="px-3 mb-3 text-[13px] font-semibold uppercase tracking-[0.14em] text-ds-paper/60">
          {SECTION_LABEL[user?.role] || "Menu"}
        </p>
        <ul className="space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `relative flex items-center gap-3.5 min-h-[44px] px-3 rounded-ds text-[16px] transition-colors
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-paper ${
                    isActive
                      ? "bg-ds-ink-2 text-white font-semibold"
                      : "text-ds-paper/80 hover:text-white hover:bg-ds-ink-2/60"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {/* Seal marker at the sidebar edge — the active nav item is one of Seal's uses. */}
                    {isActive && <span className="absolute -left-3 top-1 bottom-1 w-1 rounded-r-ds-sm bg-ds-seal" aria-hidden="true" />}
                    <Icon className="h-5 w-5 shrink-0" strokeWidth={1.8} />
                    <span>{label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="relative mx-3 mb-4 pt-4 border-t border-ds-paper/15">
        <div className="flex items-center gap-3 px-3">
          <span className="h-10 w-10 shrink-0 rounded-full bg-ds-paper text-ds-ink font-ds-serif font-medium text-[17px] flex items-center justify-center">
            {initials}
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-[16px] leading-[22px] text-white truncate">
              {user?.full_name || user?.email || "Guest"}
            </p>
            <p className="text-[14px] leading-[20px] text-ds-paper/65">{ROLE_LABEL[user?.role] || ""}</p>
          </div>
        </div>
        <button
          onClick={onSignOut}
          className="mt-2 w-full flex items-center gap-3.5 min-h-[44px] px-3 rounded-ds text-[15px] text-ds-paper/70 hover:text-white hover:bg-ds-ink-2/60 transition-colors
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-paper"
        >
          <LogOut className="h-5 w-5" strokeWidth={1.8} />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );
}

export default function AppShell({ title, subtitle, eyebrow, headerActions, bare = false, children }) {
  const { user, clear } = useAuthStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const signOut = async () => {
    // Clear the HttpOnly auth cookies server-side too; local state is cleared
    // even if the request fails (e.g. the session had already expired).
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    clear();
    navigate(ROUTES.LOGIN);
  };

  return (
    <div className="min-h-screen lg:flex bg-ds-paper text-ds-text font-ds-sans">
      <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen">
        <Sidebar user={user} onSignOut={signOut} />
      </aside>

      {/* Below lg: ink bar with a menu button; the sidebar opens as a drawer. */}
      <div className="lg:hidden flex items-center justify-between h-16 px-4 bg-ds-ink">
        <Wordmark onInk />
        <button
          onClick={() => setMenuOpen(true)}
          className="h-11 w-11 flex items-center justify-center text-ds-paper rounded-ds hover:bg-ds-ink-2"
          aria-label="Open menu"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>
      {menuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="w-72 max-w-[85vw] h-full">
            <Sidebar user={user} onNavigate={() => setMenuOpen(false)} onSignOut={signOut} />
          </div>
          <button
            className="flex-1 flex items-start justify-end p-5 bg-ds-ink/50"
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          >
            <X className="h-6 w-6 text-ds-paper" />
          </button>
        </div>
      )}

      {bare ? (
        // Full-height pages with their own columns (AI Chat): fill the
        // viewport below the mobile bar (h-16) or beside the sidebar.
        <main className="flex-1 min-w-0 flex flex-col h-[calc(100dvh-4rem)] lg:h-screen">{children}</main>
      ) : (
        <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-14">
          {/* Left-aligned column, 56px from the sidebar, max 1064px (mockups pp. 4, 8). */}
          <div className="max-w-ds-content pt-10 lg:pt-12 pb-24">
            {(title || headerActions) && (
              <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-4 mb-10 lg:mb-12">
                <div className="min-w-0">
                  {eyebrow && <p className="ds-meta mb-2">{eyebrow}</p>}
                  {title && <h1 className="ds-h1">{title}</h1>}
                  {subtitle && <p className="ds-body text-ds-text-2 mt-2">{subtitle}</p>}
                </div>
                {headerActions && <div className="flex items-center gap-3 shrink-0">{headerActions}</div>}
              </header>
            )}
            {children}
          </div>
        </main>
      )}
    </div>
  );
}
