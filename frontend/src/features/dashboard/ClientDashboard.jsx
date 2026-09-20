import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, MessageSquare, ScanLine, Search, ArrowUpRight, Loader2 } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { chatApi } from "@/features/chatbot/api";

const STATUS_META = {
  created: { dot: "bg-status-pending", label: "Created" },
  assigned: { dot: "bg-status-pending", label: "Assigned" },
  in_progress: { dot: "bg-status-active", label: "In progress" },
  hearing_scheduled: { dot: "bg-status-active", label: "Hearing scheduled" },
  closed: { dot: "bg-ink-muted", label: "Closed" },
};

const STATUS_PROGRESS = {
  created: 15,
  assigned: 35,
  in_progress: 55,
  hearing_scheduled: 80,
  closed: 100,
};

export default function ClientDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "there").split(" ")[0];

  const { data: stats } = useQuery({ queryKey: ["case-stats"], queryFn: casesApi.stats });
  const { data: cases, isLoading: loadingCases } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });
  const { data: sessions } = useQuery({ queryKey: ["chat-sessions"], queryFn: chatApi.listSessions });

  return (
    <AppShell
      title={`Welcome back, ${firstName}`}
      subtitle="Track your cases, talk to your lawyer, and ask the AI assistant"
    >
      <div className="flex flex-wrap">
        <Stat label="My cases" value={stats?.total ?? 0} helper={`${stats?.active ?? 0} active`} />
        <Stat label="In hearing" value={stats?.in_hearing ?? 0} helper="scheduled" />
        <Stat label="AI sessions" value={sessions?.length ?? 0} helper="conversations" />
        <Stat label="Closed" value={stats?.closed ?? 0} helper="all-time" last />
      </div>

      <div className="mt-10 grid gap-10 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <div className="flex items-start justify-between gap-4 mb-1">
            <h2 className="font-editorial text-xl text-ink-text">My cases</h2>
            <Link
              to={ROUTES.CASES}
              className="inline-flex items-center gap-1 text-xs text-brick hover:underline underline-offset-2"
            >
              View all <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          <p className="text-sm text-ink-muted mb-2">Status updates from your counsel</p>

          <div className="border-t border-hairline pt-1 mt-3">
            {loadingCases ? (
              <div className="flex items-center justify-center py-8 gap-2 text-ink-muted">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading...</span>
              </div>
            ) : !cases || cases.length === 0 ? (
              <div className="text-center py-8">
                <Briefcase className="h-8 w-8 text-ink-muted/50 mx-auto mb-3" />
                <p className="text-sm font-medium text-ink-text">No cases yet</p>
                <p className="text-sm text-ink-muted mt-1">
                  Your lawyer will share cases with you here.
                </p>
              </div>
            ) : (
              <ul>
                {cases.slice(0, 4).map((c) => {
                  const progress = STATUS_PROGRESS[c.status] ?? 0;
                  const meta = STATUS_META[c.status] || {};
                  return (
                    <li key={c.id} className="py-4 border-b border-hairline-subtle last:border-0">
                      <Link
                        to={ROUTES.CASE_DETAIL.replace(":id", c.id)}
                        className="block group py-1 px-2 -mx-2 hover:bg-hairline-subtle/40 transition-colors"
                      >
                        <div className="flex items-baseline justify-between gap-3">
                          <span className="text-sm font-medium text-ink-text truncate">
                            {c.title}
                          </span>
                          <span className="text-xs text-ink-muted shrink-0 inline-flex items-center gap-1.5">
                            <span className={`h-1.5 w-1.5 rounded-full ${meta.dot || "bg-ink-muted"}`} />
                            {meta.label || c.status}
                          </span>
                        </div>
                        <div className="mt-2.5">
                          <div className="flex items-center justify-between text-xs text-ink-muted mb-1">
                            <span>Progress</span>
                            <span>{progress}%</span>
                          </div>
                          <div className="h-1 bg-hairline-subtle overflow-hidden">
                            <div
                              className="h-full bg-ink-panel transition-all"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </section>

        <section>
          <h2 className="font-editorial text-xl text-ink-text mb-1">Quick actions</h2>
          <div className="border-t border-hairline pt-1 mt-3">
            <ul>
              <QuickAction to={ROUTES.CHATBOT} icon={MessageSquare} label="Ask AI legal assistant" />
              <QuickAction to={ROUTES.DOCUMENTS} icon={ScanLine} label="Upload document" />
              <QuickAction to={ROUTES.RESEARCH} icon={Search} label="Search Pakistani law" />
              <QuickAction to={ROUTES.CASES} icon={Briefcase} label="View my cases" last />
            </ul>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, helper, last = false }) {
  return (
    <div className={`flex-1 min-w-[140px] px-6 first:pl-0 py-1 ${last ? "" : "border-r border-hairline"}`}>
      <div className="text-sm text-ink-muted">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-ink-text leading-none">{value}</div>
      <div className="mt-2 text-xs text-ink-muted">{helper}</div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, label, last = false }) {
  return (
    <li className={last ? "" : "border-b border-hairline-subtle"}>
      <Link
        to={to}
        className="flex items-center gap-3 py-3.5 px-2 -mx-2 text-sm text-ink-text hover:bg-hairline-subtle/40 transition-colors"
      >
        <Icon className="h-4 w-4 text-ink-muted" />
        {label}
      </Link>
    </li>
  );
}
