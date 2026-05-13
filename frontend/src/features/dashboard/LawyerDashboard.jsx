import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Gavel,
  FileText,
  MessageSquare,
  ArrowUpRight,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import DashboardStat from "./components/DashboardStat";
import PanelCard from "./components/PanelCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { chatApi } from "@/features/chatbot/api";

const STATUS_STYLE = {
  CREATED: { variant: "outline", icon: AlertCircle },
  ASSIGNED: { variant: "secondary", icon: Clock },
  IN_PROGRESS: { variant: "default", icon: Clock },
  HEARING_SCHEDULED: { variant: "gold", icon: Gavel },
  CLOSED: { variant: "success", icon: CheckCircle2 },
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
    .filter((c) => c.status !== "CLOSED")
    .slice(0, 5);

  const inHearing = (cases || []).filter(
    (c) => c.status === "HEARING_SCHEDULED"
  );

  return (
    <DashboardLayout
      title={`Assalam-o-alaikum, ${firstName}`}
      subtitle="Live caseload from your account"
    >
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <DashboardStat
          label="Active Cases"
          value={loadingStats ? "—" : stats?.active ?? 0}
          helper={`${stats?.total ?? 0} total`}
          icon={Briefcase}
        />
        <DashboardStat
          label="In Hearing"
          value={loadingStats ? "—" : stats?.in_hearing ?? 0}
          helper="scheduled"
          icon={Gavel}
          delay={0.05}
        />
        <DashboardStat
          label="Closed"
          value={loadingStats ? "—" : stats?.closed ?? 0}
          helper="all-time"
          icon={CheckCircle2}
          delay={0.1}
        />
        <DashboardStat
          label="AI Sessions"
          value={sessions?.length ?? 0}
          helper="conversations"
          icon={MessageSquare}
          delay={0.15}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <PanelCard
          className="lg:col-span-2"
          title="Active Cases"
          description="Sorted by most recently updated"
          action={
            <Button asChild size="sm" variant="outline">
              <Link to={ROUTES.CASES}>
                View all <ArrowUpRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          }
          delay={0.1}
        >
          {loadingCases ? (
            <Skeleton />
          ) : activeCases.length === 0 ? (
            <Empty
              icon={Briefcase}
              title="No active cases yet"
              hint="Create your first case to get started."
              ctaLabel="New case"
              ctaTo={ROUTES.CASES}
            />
          ) : (
            <ul className="divide-y divide-border/40">
              {activeCases.map((c) => {
                const meta = STATUS_STYLE[c.status] || {};
                const Icon = meta.icon || Clock;
                return (
                  <li key={c.id} className="py-3 flex items-start gap-4">
                    <div className="h-9 w-9 rounded-lg bg-accent/15 text-accent flex items-center justify-center shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-muted-foreground">
                          {c.id.slice(0, 8)}
                        </span>
                        <Badge variant={meta.variant} className="text-[10px] uppercase tracking-wider">
                          {c.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="mt-1 font-semibold truncate">{c.title}</div>
                      <div className="mt-0.5 text-sm text-muted-foreground truncate">
                        {c.case_type}
                        {c.court_code && ` · ${c.court_code}`}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </PanelCard>

        <PanelCard
          title="Hearings Scheduled"
          description="Cases awaiting court date"
          delay={0.15}
        >
          {loadingCases ? (
            <Skeleton />
          ) : inHearing.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No hearings scheduled.
            </p>
          ) : (
            <ul className="space-y-3">
              {inHearing.map((c) => (
                <li
                  key={c.id}
                  className="rounded-lg border border-accent/30 bg-accent/5 p-3"
                >
                  <div className="font-semibold text-sm truncate">{c.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {c.case_type}
                    {c.court_code && ` · ${c.court_code}`}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </PanelCard>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <PanelCard
          className="lg:col-span-2"
          title="Quick Actions"
          delay={0.2}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <Button asChild variant="default" className="h-auto py-4 flex-col gap-1.5">
              <Link to={ROUTES.CHATBOT}>
                <MessageSquare className="h-5 w-5" />
                Ask AI Assistant
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-4 flex-col gap-1.5">
              <Link to={ROUTES.RESEARCH}>
                <FileText className="h-5 w-5" />
                Search Pakistani Law
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-4 flex-col gap-1.5">
              <Link to={ROUTES.DOCUMENTS}>
                <FileText className="h-5 w-5" />
                Upload Document
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-4 flex-col gap-1.5">
              <Link to={ROUTES.CASES}>
                <Briefcase className="h-5 w-5" />
                Open Caseload
              </Link>
            </Button>
          </div>
        </PanelCard>

        <PanelCard title="Recent AI Sessions" delay={0.25}>
          {!sessions || sessions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No AI conversations yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {sessions.slice(0, 5).map((s) => (
                <li key={s.id} className="text-sm">
                  <Link
                    to={ROUTES.CHATBOT}
                    className="block rounded-md p-2 hover:bg-secondary/40 transition-colors"
                  >
                    <div className="font-medium truncate">{s.title || "Untitled"}</div>
                    <div className="text-xs text-muted-foreground">
                      {s.total_messages} messages
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </PanelCard>
      </div>
    </DashboardLayout>
  );
}

function Skeleton() {
  return (
    <div className="flex items-center justify-center py-8 text-muted-foreground gap-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm">Loading...</span>
    </div>
  );
}

function Empty({ icon: Icon, title, hint, ctaLabel, ctaTo }) {
  return (
    <div className="text-center py-8">
      <Icon className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
      <p className="font-semibold text-sm">{title}</p>
      <p className="text-xs text-muted-foreground mt-1 mb-4">{hint}</p>
      {ctaLabel && (
        <Button asChild size="sm" variant="outline">
          <Link to={ctaTo}>{ctaLabel}</Link>
        </Button>
      )}
    </div>
  );
}
