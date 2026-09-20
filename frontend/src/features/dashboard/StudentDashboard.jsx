import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Search } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { chatApi } from "@/features/chatbot/api";

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "Student").split(" ")[0];

  const { data: sessions } = useQuery({ queryKey: ["chat-sessions"], queryFn: chatApi.listSessions });
  const totalMessages = (sessions || []).reduce((acc, s) => acc + (s.total_messages || 0), 0);

  return (
    <AppShell
      title={`Ready to learn, ${firstName}?`}
      subtitle="Drill scenarios, ask the AI, and explore Pakistani case law"
    >
      <div className="flex flex-wrap">
        <Stat label="AI sessions" value={sessions?.length ?? 0} helper="conversations" />
        <Stat label="AI messages" value={totalMessages} helper="lifetime" />
        <Stat label="Library" value="Live" helper="Pakistani statutes" />
        <Stat label="Practice mode" value="Soon" helper="simulator coming" last />
      </div>

      <div className="mt-10 grid gap-10 lg:grid-cols-2">
        <section>
          <h2 className="font-editorial text-xl text-ink-text mb-1">AI study buddy</h2>
          <p className="text-sm text-ink-muted mb-2">
            Stuck on a concept? The AI assistant explains Pakistani statutes, walks
            through precedents, and quizzes you on topics.
          </p>
          <div className="border-t border-hairline pt-4 mt-3">
            <AppButton to={ROUTES.CHATBOT}>
              <MessageSquare className="h-4 w-4" />
              Start a session
            </AppButton>

            {sessions && sessions.length > 0 && (
              <ul className="mt-4">
                {sessions.slice(0, 3).map((s) => (
                  <li key={s.id} className="border-b border-hairline-subtle last:border-0">
                    <Link
                      to={ROUTES.CHATBOT}
                      className="block py-3 px-2 -mx-2 hover:bg-hairline-subtle/40 transition-colors"
                    >
                      <div className="text-sm font-medium text-ink-text truncate">
                        {s.title || "Untitled"}
                      </div>
                      <div className="text-xs text-ink-muted">{s.total_messages} messages</div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section>
          <h2 className="font-editorial text-xl text-ink-text mb-1">Legal research</h2>
          <p className="text-sm text-ink-muted mb-2">
            Search statutes and judgments by meaning. Filter by court, year, and
            case type — every result links to the source passage.
          </p>
          <div className="border-t border-hairline pt-4 mt-3">
            <AppButton to={ROUTES.RESEARCH} variant="secondary">
              <Search className="h-4 w-4" />
              Search the library
            </AppButton>
            <p className="mt-4 text-xs text-ink-muted">
              Library contains seeded Pakistani statutes (PPC, Family Courts Act,
              Contract Act, Cr.P.C., MFLO, Constitution) plus landmark judgments
              from the Supreme Court and High Courts.
            </p>
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
