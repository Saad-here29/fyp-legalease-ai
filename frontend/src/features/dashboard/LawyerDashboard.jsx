import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Gavel,
  FileText,
  MessageSquare,
  ArrowUpRight,
  Loader2,
  Search,
} from "lucide-react";
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

export default function LawyerDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "Counsel").split(" ")[0];

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["case-stats"],
    queryFn: casesApi.stats,
  });

  const { data: cases, isLoading: loadingCases } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: chatApi.listSessions,
  });

  const activeCases = (cases || [])
    .filter((c) => c.status !== "closed")
    .slice(0, 5);

  const inHearing = (cases || []).filter((c) => c.status === "hearing_scheduled");

  const headerActions = (
    <div className="hidden md:flex items-center gap-2 w-64 border-b border-hairline pb-1.5">
      <Search className="h-4 w-4 text-ink-muted" />
      <input
        placeholder="Search cases, documents, statutes..."
        className="bg-transparent outline-none flex-1 text-sm text-ink-text placeholder:text-ink-muted/60"
      />
    </div>
  );

  return (
    <AppShell
      title={`Assalam-o-alaikum, ${firstName}`}
      subtitle="Live caseload from your account"
      headerActions={headerActions}
    >
      <div className="flex flex-wrap">
        <Stat
          label="Active cases"
          value={loadingStats ? "—" : stats?.active ?? 0}
          helper={`${stats?.total ?? 0} total`}
        />
        <Stat
          label="In hearing"
          value={loadingStats ? "—" : stats?.in_hearing ?? 0}
          helper="scheduled"
        />
        <Stat
          label="Closed"
          value={loadingStats ? "—" : stats?.closed ?? 0}
          helper="all-time"
        />
        <Stat
          label="AI sessions"
          value={sessions?.length ?? 0}
          helper="conversations"
          last
        />
      </div>

      <div className="mt-10 grid gap-10 lg:grid-cols-3">
        <Panel
          className="lg:col-span-2"
          title="Active cases"
          description="Sorted by most recently updated"
          action={
            <Link
              to={ROUTES.CASES}
              className="inline-flex items-center gap-1 text-xs text-brick hover:underline underline-offset-2"
            >
              View all <ArrowUpRight className="h-3 w-3" />
            </Link>
          }
        >
          {loadingCases ? (
            <LoadingRow />
          ) : activeCases.length === 0 ? (
            <EmptyRow
              icon={Briefcase}
              title="No active cases yet"
              hint="Create your first case to get started."
              ctaLabel="New case"
              ctaTo={ROUTES.CASES}
            />
          ) : (
            <ul>
              {activeCases.map((c) => {
                const meta = STATUS_META[c.status] || {};
                return (
                  <li
                    key={c.id}
                    className="py-3.5 border-b border-hairline-subtle last:border-0 flex items-start gap-3"
                  >
                    <span
                      className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${meta.dot || "bg-ink-muted"}`}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline gap-2">
                        <span className="font-medium text-ink-text truncate">
                          {c.title}
                        </span>
                        <span className="text-xs text-ink-muted shrink-0">
                          {meta.label || c.status}
                        </span>
                      </div>
                      <div className="text-sm text-ink-muted truncate">
                        {c.case_type}
                        {c.court_code && ` · ${c.court_code}`}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel title="Hearings scheduled" description="Cases awaiting court date">
          {loadingCases ? (
            <LoadingRow />
          ) : inHearing.length === 0 ? (
            <p className="text-sm text-ink-muted py-6 text-center">
              No hearings scheduled.
            </p>
          ) : (
            <ul>
              {inHearing.map((c) => (
                <li
                  key={c.id}
                  className="py-3 border-b border-hairline-subtle last:border-0"
                >
                  <div className="flex items-center gap-2 text-sm font-medium text-ink-text">
                    <Gavel className="h-3.5 w-3.5 text-ink-muted shrink-0" />
                    <span className="truncate">{c.title}</span>
                  </div>
                  <div className="text-xs text-ink-muted mt-0.5 pl-5">
                    {c.case_type}
                    {c.court_code && ` · ${c.court_code}`}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <div className="mt-10 grid gap-10 lg:grid-cols-3">
        <Panel className="lg:col-span-2" title="Quick actions">
          <ul>
            <QuickAction to={ROUTES.CHATBOT} icon={MessageSquare} label="Ask AI assistant" />
            <QuickAction to={ROUTES.RESEARCH} icon={FileText} label="Search Pakistani law" />
            <QuickAction to={ROUTES.DOCUMENTS} icon={FileText} label="Upload document" />
            <QuickAction to={ROUTES.CASES} icon={Briefcase} label="Open caseload" last />
          </ul>
        </Panel>

        <Panel title="Recent AI sessions">
          {!sessions || sessions.length === 0 ? (
            <p className="text-sm text-ink-muted text-center py-4">
              No AI conversations yet.
            </p>
          ) : (
            <ul>
              {sessions.slice(0, 5).map((s) => (
                <li key={s.id} className="border-b border-hairline-subtle last:border-0">
                  <Link
                    to={ROUTES.CHATBOT}
                    className="block py-3 px-2 -mx-2 hover:bg-hairline-subtle/40 transition-colors"
                  >
                    <div className="text-sm font-medium text-ink-text truncate">
                      {s.title || "Untitled"}
                    </div>
                    <div className="text-xs text-ink-muted">
                      {s.total_messages} messages
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, helper, last = false }) {
  return (
    <div
      className={`flex-1 min-w-[140px] px-6 first:pl-0 py-1 ${
        last ? "" : "border-r border-hairline"
      }`}
    >
      <div className="text-sm text-ink-muted">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-ink-text leading-none">{value}</div>
      <div className="mt-2 text-xs text-ink-muted">{helper}</div>
    </div>
  );
}

function Panel({ title, description, action, children, className = "" }) {
  return (
    <section className={className}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 mb-1">
          {title && <h2 className="font-editorial text-xl text-ink-text">{title}</h2>}
          {action}
        </div>
      )}
      {description && <p className="text-sm text-ink-muted mb-2">{description}</p>}
      <div className="border-t border-hairline pt-1 mt-3">{children}</div>
    </section>
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

function LoadingRow() {
  return (
    <div className="flex items-center justify-center py-8 text-ink-muted gap-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm">Loading...</span>
    </div>
  );
}

function EmptyRow({ icon: Icon, title, hint, ctaLabel, ctaTo }) {
  return (
    <div className="text-center py-8">
      <Icon className="h-8 w-8 text-ink-muted/50 mx-auto mb-3" />
      <p className="text-sm font-medium text-ink-text">{title}</p>
      <p className="text-xs text-ink-muted mt-1 mb-4">{hint}</p>
      {ctaLabel && (
        <Link to={ctaTo} className="text-xs text-brick hover:underline underline-offset-2">
          {ctaLabel}
        </Link>
      )}
    </div>
  );
}
