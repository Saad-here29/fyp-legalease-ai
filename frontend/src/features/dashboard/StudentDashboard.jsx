import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { chatApi } from "@/features/chatbot/api";
import { researchApi } from "@/features/legal-research/api";
import { RuledSection, ViewAll, SessionList } from "./components/DashParts";

// Student dashboard — design system v1, per docs/design_reference page 6.
// Adapted to what exists: no reading progress, weekly practice, saved items
// or moot folder (none are built; the Practice Simulator is future work).
// Both actions hand off to real pages: the question opens pre-filled in AI
// Chat, the search runs on the Research page.

const CONCEPTS = [
  "What is free consent under the Contract Act?",
  "How does khula differ from talaq?",
  "What is qatl-i-amd under the PPC?",
];

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const firstName = (user?.full_name || "Student").split(" ")[0];
  const [question, setQuestion] = useState("");
  const [search, setSearch] = useState("");

  const { data: sessions } = useQuery({ queryKey: ["chat-sessions"], queryFn: chatApi.listSessions });
  const { data: stats } = useQuery({ queryKey: ["research-stats"], queryFn: researchApi.stats, staleTime: Infinity });

  const ask = (q) => q.trim() && navigate(ROUTES.CHATBOT, { state: { question: q.trim() } });

  return (
    <AppShell eyebrow="Study desk" title={`Welcome back, ${firstName}.`}>
      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="ds-section">
          <p className="ds-eyebrow">Ask about a concept</p>
          <form
            className="mt-4 bg-ds-sheet border border-ds-rule rounded-ds p-5 focus-within:border-ds-ink"
            onSubmit={(e) => {
              e.preventDefault();
              ask(question);
            }}
          >
            <label htmlFor="concept-q" className="font-ds-sans font-semibold text-[15px]">Your question</label>
            <textarea
              id="concept-q"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              dir="auto"
              placeholder="e.g. What is the difference between a void agreement and a voidable contract?"
              className="mt-2 w-full resize-none bg-transparent font-ds-sans text-[17px] leading-[26px] placeholder:text-ds-text-2/70 focus:outline-none"
            />
            <div className="mt-3 flex items-center justify-between gap-4">
              <span className="ds-meta">Answers cite the statute text they rely on</span>
              <button type="submit" className="ds-btn-primary" disabled={!question.trim()}>
                Ask
              </button>
            </div>
          </form>
          <div className="mt-4 flex flex-wrap gap-2">
            {CONCEPTS.map((c) => (
              <button
                key={c}
                onClick={() => ask(c)}
                className="min-h-[44px] px-3 rounded-ds border border-ds-rule bg-ds-sheet/60 font-ds-sans text-[15px] text-ds-text text-left hover:border-ds-ink
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink"
              >
                {c}
              </button>
            ))}
          </div>
        </section>

        <section className="ds-section">
          <p className="ds-eyebrow">Search the statute library</p>
          <form
            className="mt-4 flex gap-3"
            role="search"
            onSubmit={(e) => {
              e.preventDefault();
              if (search.trim().length >= 2) navigate(`${ROUTES.RESEARCH}?q=${encodeURIComponent(search.trim())}`);
            }}
          >
            <label className="relative flex-1">
              <span className="sr-only">Search statutes</span>
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-ds-text-2" aria-hidden="true" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Statutes, sections, concepts"
                className="ds-input pl-12"
              />
            </label>
            <button type="submit" className="ds-btn-secondary min-h-[48px]" disabled={search.trim().length < 2}>
              Search
            </button>
          </form>
          <p className="ds-body text-ds-text-2 mt-4">
            Semantic search over{stats?.documents ? ` about ${stats.documents.toLocaleString()}` : ""} Pakistani legal
            documents — mostly Acts, Ordinances, Codes and Orders, including the PPC, Cr.P.C., Contract Act and family
            laws. The library holds no court judgments or case law.
          </p>
        </section>
      </div>

      <RuledSection
        title="Your recent AI chats"
        className="mt-12 max-w-[760px]"
        action={sessions?.length > 0 && <ViewAll to={ROUTES.CHATBOT}>Open AI Chat</ViewAll>}
      >
        <SessionList sessions={sessions} limit={5} />
      </RuledSection>
    </AppShell>
  );
}
