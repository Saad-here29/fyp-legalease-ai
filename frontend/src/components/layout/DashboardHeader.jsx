import { Bell, Search } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ROLES } from "@/constants";

const ROLE_BADGE_VARIANT = {
  [ROLES.LAWYER]: "default",
  [ROLES.CLIENT]: "secondary",
  [ROLES.STUDENT]: "outline",
};

export default function DashboardHeader({ title, subtitle }) {
  const { user } = useAuthStore();
  const initials =
    (user?.full_name || user?.email || "U")
      .split(/[\s@]/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-6 lg:px-10 py-4 border-b border-border/40 bg-background/70 backdrop-blur-xl">
      <div className="min-w-0">
        <h1 className="font-serif text-2xl lg:text-3xl font-bold tracking-tight truncate">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-muted-foreground mt-0.5 truncate">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg border border-border/40 bg-card/40 text-sm text-muted-foreground w-72">
          <Search className="h-4 w-4" />
          <input
            placeholder="Search cases, documents, statutes..."
            className="bg-transparent outline-none flex-1 text-foreground placeholder:text-muted-foreground"
          />
        </div>

        <button
          className="relative flex items-center justify-center h-10 w-10 rounded-lg border border-border/40 bg-card/40 hover:bg-secondary/40 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-accent" />
        </button>

        <div className="flex items-center gap-3 pl-3 border-l border-border/40">
          <div className="hidden sm:flex flex-col items-end leading-tight">
            <span className="text-sm font-semibold">
              {user?.full_name || user?.email || "Guest"}
            </span>
            <Badge
              variant={ROLE_BADGE_VARIANT[user?.role] || "outline"}
              className="mt-0.5 text-[10px] uppercase tracking-wider"
            >
              {user?.role || "GUEST"}
            </Badge>
          </div>
          <Avatar className="h-10 w-10 border border-accent/40">
            <AvatarFallback className="bg-gold-gradient text-legal-navy font-semibold">
              {initials}
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
}
