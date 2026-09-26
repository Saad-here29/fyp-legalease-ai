import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowUp, Loader2, MessageSquarePlus } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import Markdown from "@/lib/Markdown";
import { citeAnchor } from "@/lib/citations";
import { chatApi } from "./api";
import { cnInput } from "@/lib/formStyles";

const SUGGESTIONS = [
  "What is the penalty for child abuse under the Zainab Alert Act?",
  "How do I file an FIR? What does Section 154 Cr.P.C. say?",
  "Explain khula under Pakistani Family Law",
  "What is murder under Section 302 of the Pakistan Penal Code?",
];

const clock = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// Stored citations are one entry per retrieved passage, in the order the
// model was given them — so entry i is the "[i+1]" in the answer.
const numbered = (citations) =>
  (citations || []).map((c, i) => ({
    n: c.n ?? i + 1,
    source: c.source || c.title || "",
    excerpt: c.excerpt || "",
  }));

export default function ChatPage() {
  const qc = useQueryClient();
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: chatApi.listSessions,
  });

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    chatApi
      .history(sessionId)
      .then((history) => {
        setMessages(
          history.map((m) => ({
            id: m.id,
            // API sends "ai" / "user" (lowercase); the old "AI" check showed
            // every reloaded answer as a user message.
            role: String(m.sender_type).toLowerCase() === "ai" ? "assistant" : "user",
            content: m.content,
            citations: numbered(m.citations),
            elapsedMs: m.response_time_ms ?? null,
            time: clock(new Date(m.created_at)),
          }))
        );
      })
      .catch(() => setMessages([]));
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: async (payload) => {
      const t0 = performance.now();
      const data = await chatApi.sendMessage(payload);
      return { data, clientMs: Math.round(performance.now() - t0) };
    },
    onSuccess: ({ data, clientMs }) => {
      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: data.response,
          citations: numbered(data.citations),
          elapsedMs: data.response_time_ms ?? clientMs,
          time: clock(new Date()),
        },
      ]);
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    onError: (err) => {
      const apiErr = err?.response?.data?.error;
      toast.error(apiErr?.message || "AI is unavailable right now.", { description: apiErr?.hint });
    },
  });

  const submit = (e) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sendMutation.isPending) return;
    setMessages((prev) => [
      ...prev,
      { id: `me-${Date.now()}`, role: "user", content: trimmed, citations: [], time: clock(new Date()) },
    ]);
    setInput("");
    sendMutation.mutate({ message: trimmed, session_id: sessionId });
  };

  const startNew = () => {
    setSessionId(null);
    setMessages([]);
  };

  return (
    <AppShell title="AI legal assistant" subtitle="Answers from Pakistani statute text, with the passages they cite">
      <div className="grid gap-10 lg:grid-cols-[1fr_280px] h-[calc(100vh-230px)]">
        <div className="flex flex-col min-h-0">
          <div ref={scrollRef} className="flex-1 overflow-y-auto pr-2">
            <div className="max-w-3xl">
              {messages.length === 0 && !sendMutation.isPending && (
                <EmptyState onPick={(q) => setInput(q)} />
              )}

              {messages.map((m) =>
                m.role === "user" ? <Question key={m.id} message={m} /> : <Answer key={m.id} message={m} />
              )}

              {sendMutation.isPending && <Thinking />}
            </div>
          </div>

          <form onSubmit={submit} className="mt-4 max-w-3xl flex items-end gap-3 border-t border-hairline pt-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit(e);
                }
              }}
              placeholder="Ask about Pakistani law — English or Urdu"
              rows={2}
              className={cnInput(false, "flex-1 resize-none py-2 text-base")}
              disabled={sendMutation.isPending}
            />
            <AppButton type="submit" disabled={sendMutation.isPending || !input.trim()} className="shrink-0">
              {sendMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
              Ask
            </AppButton>
          </form>
        </div>

        <aside>
          <AppButton variant="secondary" onClick={startNew} className="w-full mb-8">
            <MessageSquarePlus className="h-4 w-4" />
            New conversation
          </AppButton>

          <h2 className="font-editorial text-xl text-ink-text">Recent sessions</h2>
          <div className="border-t border-hairline mt-3">
            {!sessions || sessions.length === 0 ? (
              <p className="type-meta pt-3">Your conversations will appear here.</p>
            ) : (
              <ul>
                {sessions.slice(0, 8).map((s) => (
                  <li key={s.id} className="border-b border-hairline-subtle last:border-0">
                    <button
                      onClick={() => setSessionId(s.id)}
                      className={`w-full text-left py-3 px-2 -mx-2 text-ink-text transition-colors ${
                        sessionId === s.id ? "bg-hairline-subtle/60" : "hover:bg-hairline-subtle/40"
                      }`}
                    >
                      <div className="text-[15px] font-medium truncate">{s.title || "Untitled"}</div>
                      <div className="type-meta">{s.total_messages} messages</div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

function Question({ message }) {
  return (
    <div className="pt-8 first:pt-2">
      <p className="type-meta mb-1.5">You · {message.time}</p>
      <p className="text-lg font-medium text-ink-text leading-snug whitespace-pre-wrap">{message.content}</p>
    </div>
  );
}

function Answer({ message }) {
  // Only passages the answer actually cites get a footnote, keeping their
  // original numbers so "[3]" in the text always means footnote 3.
  const cited = new Set(
    [...message.content.matchAll(/\[(\d{1,2})\](?!\()/g)].map((m) => Number(m[1]))
  );
  const footnotes = message.citations.filter((c) => cited.has(c.n));
  // Some statutes are indexed under two titles, one OCR-damaged ("Muslim
  // Family Laws Ordinance, 1961" / "THE MUSLIM FAMILY LAWS ORDINAN CE,
  // 1961"): compare letters and digits only so they count once.
  const statutes = new Set(
    footnotes.map((c) => c.source.toLowerCase().replace(/[^a-z0-9]/g, "").replace(/^the/, ""))
  ).size;

  const meta = [
    statutes ? `${statutes} statute${statutes === 1 ? "" : "s"}` : null,
    message.elapsedMs != null ? `${(message.elapsedMs / 1000).toFixed(1)}s` : null,
    message.time,
  ].filter(Boolean);

  return (
    <article className="pt-4 pb-8 border-b border-hairline-subtle">
      <Markdown citeId={message.id}>{message.content}</Markdown>

      <p className="type-meta mt-4">{meta.join(" · ")}</p>

      {footnotes.length > 0 && (
        <ol className="mt-3 pt-3 border-t border-hairline-subtle space-y-2">
          {footnotes.map((c) => (
            <li key={c.n} id={citeAnchor(message.id, c.n)} className="flex gap-3 text-sm scroll-mt-4">
              <span className="text-brick font-semibold w-4 shrink-0 text-right">{c.n}</span>
              <span className="min-w-0">
                <span className="text-ink-text font-medium">{c.source}</span>
                {c.excerpt && (
                  <span className="block text-ink-muted line-clamp-2 mt-0.5">{c.excerpt}</span>
                )}
              </span>
            </li>
          ))}
        </ol>
      )}
    </article>
  );
}

function Thinking() {
  return (
    <div className="flex items-center gap-2.5 pt-4 pb-8 type-meta">
      <Loader2 className="h-4 w-4 animate-spin" />
      Searching the statute library and drafting an answer…
    </div>
  );
}

function EmptyState({ onPick }) {
  return (
    <div className="py-6">
      <p className="eyebrow mb-3">Pakistani statute law</p>
      <h3 className="type-title">Ask a legal question.</h3>
      <p className="type-lead mt-4 max-w-2xl">
        Answers are grounded in LegalEase&apos;s library of Pakistani statute text
        (Acts, Ordinances, Codes and Orders) and cite the passages they rely on.
        The library holds no court judgments or case law, and questions outside
        Pakistani law are refused.
      </p>

      <p className="type-meta mt-10 mb-2">Try one of these</p>
      <ul className="border-t border-hairline">
        {SUGGESTIONS.map((s) => (
          <li key={s} className="border-b border-hairline-subtle">
            <button
              onClick={() => onPick(s)}
              className="w-full text-left text-base text-ink-text hover:bg-hairline-subtle/40 px-2 -mx-2 py-3.5 transition-colors"
            >
              {s}
            </button>
          </li>
        ))}
      </ul>
      <p className="type-meta mt-6">English &amp; Urdu</p>
    </div>
  );
}
