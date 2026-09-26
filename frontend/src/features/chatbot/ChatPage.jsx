import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AlertTriangle, Check, List, Loader2, X } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ArchMark } from "@/components/common/Wordmark";
import Markdown from "@/lib/Markdown";
import { citeAnchor, normalizeMarkers } from "@/lib/citations";
import { chatApi } from "./api";

// AI Chat — design system v1, per the AI Chat mockup (docs/design_reference
// page 10): conversations column, then the thread with a ruled answer, a
// verification line and its sources. Adapted to what exists: no scope /
// linked-case tags, no "Save to case", no attachments and no "Open at
// section" links (none of these are built).

const SUGGESTIONS = [
  "What is the penalty for child abuse under the Zainab Alert Act?",
  "How do I file an FIR? What does Section 154 Cr.P.C. say?",
  "Explain khula under Pakistani Family Law",
  "What is murder under Section 302 of the Pakistan Penal Code?",
];

// The backend's citation check (backend/app/ai/citation_check.py) marks any
// section reference it can't find in the retrieved text with this flag.
const UNVERIFIED_FLAG = /\((?:unverified|غیر مصدقہ)\)/;

// Substantive answers open with one "Short answer:" sentence (system prompt
// in backend/app/services/legal_chat_service.py), shown as a highlighted box.
// Seen as "Short answer: …" and "**Short answer:** …". Answers without it —
// refusals, older answers — render as plain text.
const SHORT_ANSWER = /^\s*(?:\*\*)?\s*(Short answer|مختصر جواب)\s*:\s*(?:\*\*)?\s*/i;

const splitShortAnswer = (content) => {
  const m = content.match(SHORT_ANSWER);
  if (!m) return { label: null, short: null, rest: content };
  const body = content.slice(m[0].length);
  const end = body.indexOf("\n");
  const short = (end === -1 ? body : body.slice(0, end)).trim();
  if (!short) return { label: null, short: null, rest: content };
  return { label: m[1], short, rest: end === -1 ? "" : body.slice(end).trim() };
};

const clock = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const dayLabel = (iso) => {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
};

// Stored citations are one entry per retrieved passage, in the order the
// model was given them — so entry i is the "[i+1]" in the answer.
const numbered = (citations) =>
  (citations || []).map((c, i) => ({
    n: c.n ?? i + 1,
    source: c.source || c.title || "",
    // Stored excerpts start wherever the indexed chunk starts, often
    // mid-sentence (", which amount…"): drop the leading punctuation.
    excerpt: (c.excerpt || "").replace(/^[\s,;:.)\]-]+/, ""),
  }));

export default function ChatPage() {
  const qc = useQueryClient();
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [listOpen, setListOpen] = useState(false); // conversations, below lg
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
            // API sends "ai" / "user" (lowercase).
            role: String(m.sender_type).toLowerCase() === "ai" ? "assistant" : "user",
            content: normalizeMarkers(m.content),
            citations: numbered(m.citations),
            elapsedMs: m.response_time_ms ?? null,
            time: clock(new Date(m.created_at)),
          }))
        );
      })
      .catch(() => setMessages([]));
  }, [sessionId]);

  useEffect(() => {
    // Follow the thread to its newest message; leave the empty state at the top.
    if (messages.length === 0) return;
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
          content: normalizeMarkers(data.response),
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

  const openSession = (id) => {
    setSessionId(id);
    setListOpen(false);
  };
  const startNew = () => openSession(null);

  const current = sessions?.find((s) => s.id === sessionId);
  // Until the refreshed session list arrives, a new thread is titled by its
  // first question (the backend titles sessions the same way).
  const firstQuestion = messages.find((m) => m.role === "user")?.content;
  const threadTitle = current?.title || firstQuestion || "New conversation";

  return (
    <AppShell bare>
      <div className="relative flex-1 min-h-0 flex">
        {/* Conversations */}
        <aside
          className={`${listOpen ? "flex" : "hidden"} lg:flex absolute inset-0 z-10 lg:static lg:w-[300px] shrink-0
            flex-col bg-ds-paper border-r border-ds-rule`}
          aria-label="Conversations"
        >
          <div className="h-[72px] shrink-0 flex items-center justify-between gap-3 px-6 border-b border-ds-rule">
            <h2 className="font-ds-sans font-semibold text-[20px] leading-[28px]">Conversations</h2>
            <div className="flex items-center gap-2">
              <button onClick={startNew} className="ds-btn-secondary px-4">
                New
              </button>
              <button
                onClick={() => setListOpen(false)}
                className="lg:hidden h-11 w-11 flex items-center justify-center rounded-ds hover:bg-ds-sheet"
                aria-label="Close conversations"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {!sessions || sessions.length === 0 ? (
              <p className="ds-meta px-6 py-5">Your conversations will appear here.</p>
            ) : (
              <ul>
                {sessions.map((s) => {
                  const active = s.id === sessionId;
                  return (
                    <li key={s.id} className="border-b border-ds-rule">
                      <button
                        onClick={() => openSession(s.id)}
                        aria-current={active ? "true" : undefined}
                        className={`relative w-full text-left px-6 py-4 min-h-[72px] transition-colors
                          focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ds-ink ${
                          active ? "bg-ds-sheet" : "hover:bg-ds-sheet/60"
                        }`}
                      >
                        {/* Seal marks the open conversation — an active-item use of Seal. */}
                        {active && <span className="absolute left-0 inset-y-0 w-1 bg-ds-seal" aria-hidden="true" />}
                        <span className={`block text-[16px] leading-[24px] line-clamp-2 ${active ? "font-semibold" : ""}`} dir="auto">
                          {s.title || "Untitled"}
                        </span>
                        <span className="ds-meta block mt-1">
                          {dayLabel(s.updated_at)} · {s.total_messages} message{s.total_messages === 1 ? "" : "s"}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </aside>

        {/* Thread */}
        <section className="flex-1 min-w-0 flex flex-col">
          <header className="h-[72px] shrink-0 flex items-center gap-3 px-4 sm:px-6 lg:px-11 border-b border-ds-rule">
            <button
              onClick={() => setListOpen(true)}
              className="lg:hidden h-11 w-11 -ml-2 flex items-center justify-center rounded-ds hover:bg-ds-sheet"
              aria-label="Show conversations"
            >
              <List className="h-5 w-5" />
            </button>
            <h1 className="font-ds-sans font-semibold text-[20px] leading-[28px] truncate" dir="auto">
              {threadTitle}
            </h1>
          </header>

          <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
            <div className="max-w-[800px] px-4 sm:px-6 lg:px-11 py-10 space-y-10">
              {messages.length === 0 && !sendMutation.isPending && <EmptyState onPick={setInput} />}

              {messages.map((m) =>
                m.role === "user" ? <Question key={m.id} message={m} /> : <Answer key={m.id} message={m} />
              )}

              {sendMutation.isPending && <Thinking />}
            </div>
          </div>

          <div className="shrink-0 border-t border-ds-rule px-4 sm:px-6 lg:px-11 pt-5 pb-5">
            <form
              onSubmit={submit}
              className="max-w-[756px] flex items-end gap-3 p-3 bg-ds-sheet border border-ds-rule rounded-ds focus-within:border-ds-ink"
            >
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submit(e);
                  }
                }}
                placeholder={messages.length ? "Ask a follow-up…" : "Ask about Pakistani law — English or Urdu"}
                aria-label="Your question"
                rows={2}
                dir="auto"
                className="flex-1 min-h-[52px] max-h-40 resize-none bg-transparent px-2 py-1 font-ds-sans text-[17px] leading-[26px]
                  text-ds-text placeholder:text-ds-text-2/70 focus:outline-none"
                disabled={sendMutation.isPending}
              />
              <button type="submit" className="ds-btn-primary shrink-0" disabled={sendMutation.isPending || !input.trim()}>
                {sendMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Waiting for answer" /> : "Ask"}
              </button>
            </form>
            <p className="ds-meta mt-3">
              Answers cite the statute text they rely on. Read the source before relying on it in court.
            </p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Question({ message }) {
  return (
    <div className="bg-ds-rule/40 rounded-ds px-6 py-5">
      <p className="font-ds-sans font-semibold text-[14px] leading-[20px] text-ds-text-2">You</p>
      <p className="mt-1.5 text-[17px] leading-[28px] text-ds-text whitespace-pre-wrap" dir="auto">
        {message.content}
      </p>
    </div>
  );
}

function AiLabel() {
  return (
    <div className="flex items-center gap-3">
      <span className="h-8 w-8 rounded-ds-sm bg-ds-ink text-ds-paper flex items-center justify-center" aria-hidden="true">
        <ArchMark className="h-4 w-4" />
      </span>
      <span className="font-ds-sans font-semibold text-[15px] text-ds-text-2">LegalEase AI</span>
    </div>
  );
}

function Answer({ message }) {
  // Only passages the answer actually cites are listed, keeping their
  // original numbers so "[3]" in the text always means source 3.
  const cited = new Set([...message.content.matchAll(/\[(\d{1,2})\](?!\()/g)].map((m) => Number(m[1])));
  const sources = message.citations.filter((c) => cited.has(c.n));
  // Some statutes are indexed under two titles, one OCR-damaged ("Muslim
  // Family Laws Ordinance, 1961" / "THE MUSLIM FAMILY LAWS ORDINAN CE,
  // 1961"): compare letters and digits only so they count once.
  const statutes = new Set(
    sources.map((c) => c.source.toLowerCase().replace(/[^a-z0-9]/g, "").replace(/^the/, ""))
  ).size;
  const flagged = UNVERIFIED_FLAG.test(message.content);
  const { label, short, rest } = splitShortAnswer(message.content);

  const meta = [
    statutes ? `${statutes} statute${statutes === 1 ? "" : "s"}` : null,
    message.elapsedMs != null ? `${(message.elapsedMs / 1000).toFixed(1)}s` : null,
    message.time,
  ].filter(Boolean);

  const copy = () =>
    navigator.clipboard
      .writeText(message.content)
      .then(() => toast.success("Answer copied"))
      .catch(() => toast.error("Couldn't copy — select the text instead."));

  return (
    <article>
      <AiLabel />
      {label ? (
        <>
          <div className="mt-4 border-t-2 border-ds-ink border-x border-b border-x-ds-rule border-b-ds-rule bg-ds-sheet px-6 py-5" dir="auto">
            <p className="font-ds-sans font-semibold text-[15px] leading-[20px] text-ds-text-2">{label}</p>
            <Markdown citeId={message.id} variant="ds" className="mt-1.5 prose-p:my-0 text-[19px] leading-[30px] font-medium">
              {short}
            </Markdown>
          </div>
          {rest && (
            <div className="mt-6" dir="auto">
              <Markdown citeId={message.id} variant="ds">
                {rest}
              </Markdown>
            </div>
          )}
        </>
      ) : (
        <div className="mt-4 border-t-2 border-ds-ink pt-6" dir="auto">
          <Markdown citeId={message.id} variant="ds">
            {message.content}
          </Markdown>
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
        <p className="ds-meta flex flex-wrap items-center gap-x-2">
          <span>{meta.join(" · ")}</span>
          {/* Only answers that cite sources went through the check with something to check. */}
          {sources.length > 0 &&
            (flagged ? (
              <span className="inline-flex items-center gap-1.5 font-semibold text-ds-review">
                · <AlertTriangle className="h-4 w-4" strokeWidth={2.25} /> Some references unverified — see the note in the answer
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-semibold text-ds-pass">
                · <Check className="h-4 w-4" strokeWidth={2.5} /> Checked against source
              </span>
            ))}
        </p>
        <button
          onClick={copy}
          className="min-h-[44px] px-2 -mx-2 font-ds-sans font-semibold text-[15px] text-ds-text rounded-ds hover:bg-ds-sheet
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink"
        >
          Copy
        </button>
      </div>

      {sources.length > 0 && (
        <div className="mt-4 pt-5 border-t border-ds-rule">
          <p className="ds-eyebrow">Sources</p>
          <ol className="mt-2">
            {sources.map((c) => (
              <li
                key={c.n}
                id={citeAnchor(message.id, c.n)}
                className="grid grid-cols-[36px_1fr] gap-x-2 py-4 border-b border-ds-rule last:border-0 scroll-mt-4"
              >
                <span className="font-ds-sans font-semibold text-[16px] leading-[24px] text-ds-text">[{c.n}]</span>
                <span className="min-w-0">
                  <span className="block font-ds-sans font-semibold text-[16px] leading-[24px] text-ds-text">{c.source}</span>
                  {c.excerpt && <span className="ds-meta block mt-1 line-clamp-2" dir="auto">{c.excerpt}</span>}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </article>
  );
}

function Thinking() {
  return (
    <div>
      <AiLabel />
      <p className="mt-4 border-t-2 border-ds-ink pt-6 flex items-center gap-3 ds-body text-ds-text-2">
        <Loader2 className="h-5 w-5 animate-spin" />
        Searching the statute library and drafting an answer…
      </p>
    </div>
  );
}

function EmptyState({ onPick }) {
  return (
    <div>
      <p className="ds-eyebrow">Pakistani statute law</p>
      <h2 className="ds-h2 mt-3">Ask a legal question.</h2>
      <p className="ds-body text-ds-text-2 mt-4 max-w-[640px]">
        Answers are grounded in LegalEase&apos;s library of Pakistani statute text (Acts, Ordinances, Codes and
        Orders) and cite the passages they rely on. The library holds no court judgments or case law, and questions
        outside Pakistani law are refused.
      </p>

      <p className="ds-meta mt-10 mb-3">Try one of these</p>
      <ul className="border-t-2 border-ds-ink">
        {SUGGESTIONS.map((s) => (
          <li key={s} className="border-b border-ds-rule">
            <button
              onClick={() => onPick(s)}
              className="w-full text-left min-h-[56px] py-3.5 px-2 -mx-2 ds-body rounded-ds hover:bg-ds-sheet
                focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink"
            >
              {s}
            </button>
          </li>
        ))}
      </ul>
      <p className="ds-meta mt-5">English and Urdu</p>
    </div>
  );
}
