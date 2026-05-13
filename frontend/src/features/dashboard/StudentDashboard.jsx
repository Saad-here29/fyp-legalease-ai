import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  GraduationCap,
  MessageSquare,
  Search,
  BookOpen,
  Sparkles,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import DashboardStat from "./components/DashboardStat";
import PanelCard from "./components/PanelCard";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { chatApi } from "@/features/chatbot/api";

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "Student").split(" ")[0];

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: chatApi.listSessions,
  });

  const totalMessages = (sessions || []).reduce(
    (acc, s) => acc + (s.total_messages || 0),
    0
  );

  return (
    <DashboardLayout
      title={`Ready to learn, ${firstName}?`}
      subtitle="Drill scenarios, ask the AI, and explore Pakistani case law"
    >
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <DashboardStat
          label="AI Sessions"
          value={sessions?.length ?? 0}
          helper="conversations"
          icon={MessageSquare}
        />
        <DashboardStat
          label="AI Messages"
          value={totalMessages}
          helper="lifetime"
          icon={Sparkles}
          delay={0.05}
        />
        <DashboardStat
          label="Library"
          value="Live"
          helper="Pakistani statutes"
          icon={BookOpen}
          delay={0.1}
        />
        <DashboardStat
          label="Practice Mode"
          value="Soon"
          helper="simulator coming"
          icon={GraduationCap}
          delay={0.15}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PanelCard
          title="AI Study Buddy"
          description="Stuck on a concept? The AI assistant explains Pakistani statutes, walks through precedents, and quizzes you on topics."
          delay={0.2}
        >
          <Button asChild className="w-full" variant="gold">
            <Link to={ROUTES.CHATBOT}>
              <MessageSquare className="h-4 w-4" />
              Start a session
            </Link>
          </Button>

          {sessions && sessions.length > 0 && (
            <ul className="mt-4 space-y-2">
              {sessions.slice(0, 3).map((s) => (
                <li key={s.id}>
                  <Link
                    to={ROUTES.CHATBOT}
                    className="block rounded-md p-2 text-sm hover:bg-secondary/40 transition-colors"
                  >
                    <div className="font-medium truncate">
                      {s.title || "Untitled"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {s.total_messages} messages
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </PanelCard>

        <PanelCard
          title="Legal Research"
          description="Search statutes and judgments by meaning. Filter by court, year, and case type — every result links to the source passage."
          delay={0.25}
        >
          <Button asChild className="w-full" variant="outline">
            <Link to={ROUTES.RESEARCH}>
              <Search className="h-4 w-4" />
              Search the library
            </Link>
          </Button>
          <p className="mt-4 text-xs text-muted-foreground">
            Library contains seeded Pakistani statutes (PPC, Family Courts Act,
            Contract Act, Cr.P.C., MFLO, Constitution) plus landmark judgments
            from the Supreme Court and High Courts.
          </p>
        </PanelCard>
      </div>
    </DashboardLayout>
  );
}
