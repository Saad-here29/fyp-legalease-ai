import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  FileText,
  MessageSquare,
  ScanLine,
  Search,
  ArrowUpRight,
  Loader2,
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

const STATUS_PROGRESS = {
  CREATED: 15,
  ASSIGNED: 35,
  IN_PROGRESS: 55,
  HEARING_SCHEDULED: 80,
  CLOSED: 100,
};

export default function ClientDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "there").split(" ")[0];

  const { data: stats } = useQuery({
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

  return (
    <DashboardLayout
      title={`Welcome back, ${firstName}`}
      subtitle="Track your cases, talk to your lawyer, and ask the AI assistant"
    >
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <DashboardStat
          label="My Cases"
          value={stats?.total ?? 0}
          helper={`${stats?.active ?? 0} active`}
          icon={Briefcase}
        />
        <DashboardStat
          label="In Hearing"
          value={stats?.in_hearing ?? 0}
          helper="scheduled"
          icon={Briefcase}
          delay={0.05}
        />
        <DashboardStat
          label="AI Sessions"
          value={sessions?.length ?? 0}
          helper="conversations"
          icon={MessageSquare}
          delay={0.1}
        />
        <DashboardStat
          label="Closed"
          value={stats?.closed ?? 0}
          helper="all-time"
          icon={FileText}
          delay={0.15}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <PanelCard
          className="lg:col-span-2"
          title="My Cases"
          description="Status updates from your counsel"
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
            <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading...</span>
            </div>
          ) : !cases || cases.length === 0 ? (
            <div className="text-center py-8">
              <Briefcase className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
              <p className="font-semibold text-sm">No cases yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Your lawyer will share cases with you here.
              </p>
            </div>
          ) : (
            <ul className="space-y-5">
              {cases.slice(0, 4).map((c) => {
                const progress = STATUS_PROGRESS[c.status] ?? 0;
                return (
                  <li
                    key={c.id}
                  >
                    <Link 
                      to={ROUTES.CASE_DETAIL.replace(":id", c.id)}
                      className="block rounded-lg border border-border/40 bg-background/30 p-4 hover:border-accent/40 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-xs font-mono text-muted-foreground">
                            {c.id.slice(0, 8)}
                          </div>
                          <div className="font-semibold mt-0.5">{c.title}</div>
                        </div>
                        <Badge className="text-[10px] uppercase tracking-wider">
                          {c.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
                          <span>Progress</span>
                          <span>{progress}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-secondary/60 overflow-hidden">
                          <div
                            className="h-full bg-gold-gradient transition-all"
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
        </PanelCard>

        <PanelCard title="Quick Actions" delay={0.15}>
          <div className="space-y-2">
            <Button asChild className="w-full justify-start" variant="default">
              <Link to={ROUTES.CHATBOT}>
                <MessageSquare className="mr-2 h-4 w-4" />
                Ask AI Legal Assistant
              </Link>
            </Button>
            <Button asChild className="w-full justify-start" variant="outline">
              <Link to={ROUTES.DOCUMENTS}>
                <ScanLine className="mr-2 h-4 w-4" />
                Upload Document
              </Link>
            </Button>
            <Button asChild className="w-full justify-start" variant="outline">
              <Link to={ROUTES.RESEARCH}>
                <Search className="mr-2 h-4 w-4" />
                Search Pakistani Law
              </Link>
            </Button>
            <Button asChild className="w-full justify-start" variant="outline">
              <Link to={ROUTES.CASES}>
                <Briefcase className="mr-2 h-4 w-4" />
                View My Cases
              </Link>
            </Button>
          </div>
        </PanelCard>
      </div>
    </DashboardLayout>
  );
}
