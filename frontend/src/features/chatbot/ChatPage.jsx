import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AlertTriangle, Check, List, Loader2, Scale, X } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ArchMark } from "@/components/common/Wordmark";
import Markdown from "@/lib/Markdown";
import { citeAnchor, normalizeMarkers } from "@/lib/citations";
import { KbSourceLink } from "@/features/knowledge-base/kbParts";
import { sectionLabel, judgmentPath } from "@/features/knowledge-base/kbFormat";
import { chatApi } from "./api";
import { researchApi } from "@/features/legal-research/api";
import { useJudgmentsInfo } from "@/features/knowledge-base/useJudgments";

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
// Every source number the answer cites, short answer included: "[3]", and
// grouped forms "[1, 2]" and "[1-3]" (older answers; new ones are normalised
// to "[1][2]" by the backend).
function citedNumbers(content) {
  const out = new Set();
  for (const m of content.matchAll(/\[(\d{1,2}(?:\s*[,–—-]\s*\d{1,2})*)\](?!\()/g)) {
    for (const part of m[1].split(",")) {
      const [a, b] = part.split(/[–—-]/).map((x) => Number(x.trim()));
      if (b && b > a && b - a <= 10) for (let n = a; n <= b; n += 1) out.add(n);
      else out.add(a);
    }
  }
  return out;
}

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

// Answers whose best passage only just passed the relevance threshold
// (backend answer_flags, LOW_CONFIDENCE_NOTE). Shown in the answer's language.
const WEAK_MATCH = {
  en: "Weak match: the closest passages in the library only partly match this question. Check the cited sections before relying on this answer.",
  ur: "کمزور مطابقت: لائبریری کے قریب ترین اقتباسات اس سوال سے جزوی طور پر ہی مطابقت رکھتے ہیں۔ اس جواب پر انحصار سے پہلے حوالہ شدہ دفعات دیکھ لیں۔",
};
const isUrdu = (text) => {
  const letters = (text || "").replace(/[^\p{L}]/gu, "");
  return letters.length > 0 && (letters.match(/[\u0600-\u06FF]/g) || []).length > letters.length / 2;
};

// The page's "Family law" switch (remembered per browser): on = the backend
// searches the family-law statutes first for family questions ("auto").
const FAMILY_KEY = "legalease.chat.familyLaw";
const readFamilyPref = () => {
  try {
    return localStorage.getItem(FAMILY_KEY) !== "off";
  } catch {
    return true;
  }
};
const toMessage = (m, extra = {}) => ({
  confidence: m.confidence ?? null,
  familyScope: Boolean(m.family_scope),
  ...extra,
});

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
// model was given them — so entry i is the "[i+1]" in the answer. Judgment
// paragraphs (kb-v2 C2) are stored after them as kind "case_law" and listed
// separately (caseLaw), never numbered.
const numbered = (citations) =>
  (citations || []).filter((c) => c.kind !== "case_law").map((c, i) => ({
    n: c.n ?? i + 1,
    source: c.source || c.title || "",
    // Stored excerpts start wherever the indexed chunk starts, often
    // mid-sentence (", which amount…"): drop the leading punctuation.
    excerpt: (c.excerpt || "").replace(/^[\s,;:.)\]-]+/, ""),
    // Knowledge-base v2 passages also say where they come from.
    section: c.section || null,
    heading: c.heading || null,
    sourceUrl: c.source_url || null,
    recordId: c.doc_id || null,
  }));

// Judgment paragraphs given to the answer, from the live reply's case_law or
// the stored citations. Weak matches (under 0.55) are never shown.
const caseLaw = (list) =>
  (list || [])
    .filter((c) => (c.relevance ?? 1) >= 0.55)
    .map((c) => ({
      docId: c.doc_id,
      name: c.source,
      court: c.court || null,
      year: c.year || null,
      caseNumber: c.case_number || null,
      paragraph: c.paragraph,
      excerpt: (c.excerpt || "").trim(),
    }));

export default function ChatPage() {
  const qc = useQueryClient();
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const location = useLocation();
  // A question handed over from elsewhere (the student dashboard's "Ask
  // about a concept") is pre-filled, not sent — the user presses Ask.
  const [input, setInput] = useState(location.state?.question || "");
  const [listOpen, setListOpen] = useState(false); // conversations, below lg
  const [familyLaw, setFamilyLaw] = useState(readFamilyPref);
  const scrollRef = useRef(null);

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: chatApi.listSessions,
  });
  // The switch exists only when the backend has the family-law index on.
  const { data: options } = useQuery({
    queryKey: ["chat-options"],
    queryFn: chatApi.options,
    staleTime: Infinity,
  });
  const familyAvailable = Boolean(options?.family_index);

  const toggleFamily = () => {
    setFamilyLaw((on) => {
      try {
        localStorage.setItem(FAMILY_KEY, on ? "off" : "on");
      } catch {
        /* private mode: the choice lasts until reload */
      }
      return !on;
    });
  };

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    chatApi
      .history(sessionId)
      .then((history) => {
        setMessages(
          history.map((m) =>
            toMessage(m, {
              id: m.id,
              // API sends "ai" / "user" (lowercase).
              role: String(m.sender_type).toLowerCase() === "ai" ? "assistant" : "user",
              content: normalizeMarkers(m.content),
              citations: numbered(m.citations),
              caseLaw: caseLaw((m.citations || []).filter((c) => c.kind === "case_law")),
              elapsedMs: m.response_time_ms ?? null,
              time: clock(new Date(m.created_at)),
            })
          )
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
        toMessage(data, {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: normalizeMarkers(data.response),
          citations: numbered(data.citations),
          caseLaw: caseLaw(data.case_law),
          elapsedMs: data.response_time_ms ?? clientMs,
          time: clock(new Date()),
        }),
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
    sendMutation.mutate({
      message: trimmed,
      session_id: sessionId,
      ...(familyAvailable ? { family: familyLaw ? "auto" : "off" } : {}),
    });
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
            <h1 className="flex-1 min-w-0 font-ds-sans font-semibold text-[20px] leading-[28px] truncate" dir="auto">
              {threadTitle}
            </h1>
            {familyAvailable && (
              <button
                type="button"
                role="switch"
                aria-checked={familyLaw}
                onClick={toggleFamily}
                title={
                  familyLaw
                    ? "Family-law questions search the family statutes first (MFLO, Family Courts Act, Dowry Act…)"
                    : "Family-law focus is off: every question searches the whole library"
                }
                className="shrink-0 min-h-[44px] inline-flex items-center gap-2 px-3 rounded-ds font-ds-sans font-semibold text-[15px]
                  text-ds-text hover:bg-ds-sheet focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink"
              >
                <span
                  aria-hidden="true"
                  className={`relative h-6 w-10 rounded-full border-2 transition-colors ${
                    familyLaw ? "bg-ds-ink border-ds-ink" : "bg-ds-paper border-ds-rule"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-4 w-4 rounded-full transition-all ${
                      familyLaw ? "left-[18px] bg-ds-paper" : "left-0.5 bg-ds-text-2"
                    }`}
                  />
                </span>
                Family law
              </button>
            )}
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
  const cited = citedNumbers(message.content);
  const sources = message.citations.filter((c) => cited.has(c.n));
  // Some statutes are indexed under two titles, one OCR-damaged ("Muslim
  // Family Laws Ordinance, 1961" / "THE MUSLIM FAMILY LAWS ORDINAN CE,
  // 1961"): compare letters and digits only so they count once.
  const statutes = new Set(
    sources.map((c) => c.source.toLowerCase().replace(/[^a-z0-9]/g, "").replace(/^the/, ""))
  ).size;
  const flagged = UNVERIFIED_FLAG.test(message.content);
  const { label, short, rest } = splitShortAnswer(message.content);

  const weak = message.confidence === "low";
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
      {weak && (
        <p
          className="mt-4 flex items-start gap-2 bg-ds-review-tint text-ds-review px-4 py-3 rounded-ds font-ds-sans font-semibold text-[15px] leading-[22px]"
          dir="auto"
          role="note"
        >
          <AlertTriangle className="h-4 w-4 mt-[3px] shrink-0" strokeWidth={2.25} aria-hidden="true" />
          {WEAK_MATCH[isUrdu(message.content) ? "ur" : "en"]}
        </p>
      )}
      {label ? (
        <>
          <div className="mt-4 border-t-2 border-ds-ink border-x border-b border-x-ds-rule border-b-ds-rule bg-ds-sheet px-6 py-5" dir="auto">
            <p className="font-ds-sans font-semibold text-[15px] leading-[20px] text-ds-text-2">{label}</p>
            <Markdown citeId={message.id} className="mt-1.5 prose-p:my-0 text-[19px] leading-[30px] font-medium">
              {short}
            </Markdown>
          </div>
          {rest && (
            <div className="mt-6" dir="auto">
              <Markdown citeId={message.id}>
                {rest}
              </Markdown>
            </div>
          )}
        </>
      ) : (
        <div className="mt-4 border-t-2 border-ds-ink pt-6" dir="auto">
          <Markdown citeId={message.id}>
            {message.content}
          </Markdown>
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
        <p className="ds-meta flex flex-wrap items-center gap-x-2">
          <span>{meta.join(" · ")}</span>
          {message.familyScope && (
            <span className="inline-flex items-center gap-1.5 font-semibold text-ds-text">
              · <Scale className="h-4 w-4" strokeWidth={2.25} aria-hidden="true" /> Family-law statutes
            </span>
          )}
          {/* Only answers that cite sources went through the check with something to check. */}
          {sources.length > 0 &&
            (flagged ? (
              <span className="inline-flex items-center gap-1.5 font-semibold text-ds-review">
                · <AlertTriangle className="h-4 w-4" strokeWidth={2.25} /> Some references unverified — see the note in the answer
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-semibold text-ds-pass">
                · <Check className="h-4 w-4" strokeWidth={2.5} /> No unverified section references
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
                  <span className="block font-ds-sans font-semibold text-[16px] leading-[24px] text-ds-text">
                    {c.section || c.heading ? `${c.source} - ${sectionLabel(c.section, c.heading)}` : c.source}
                  </span>
                  {c.excerpt && <span className="ds-meta block mt-1 line-clamp-2" dir="auto">{c.excerpt}</span>}
                  {(c.sourceUrl || c.recordId) && (
                    <span className="block mt-2">
                      <KbSourceLink sourceUrl={c.sourceUrl} recordId={c.recordId} />
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {message.caseLaw?.length > 0 && (
        <div className="mt-4 pt-5 border-t border-ds-rule">
          <p className="ds-eyebrow">Case law</p>
          <p className="ds-meta mt-1">
            Paragraphs from past judgments given to this answer as context (team-supplied dataset, staged).
          </p>
          <ul className="mt-2">
            {message.caseLaw.map((c) => (
              <li key={`${c.docId}-${c.paragraph}`} className="py-4 border-b border-ds-rule last:border-0">
                <span className="block font-ds-sans font-semibold text-[16px] leading-[24px] text-ds-text">
                  {c.name}
                  {c.name.includes(`(${[c.court, c.year].filter(Boolean).join(", ")})`) || (!c.court && !c.year)
                    ? ""
                    : ` (${[c.court, c.year].filter(Boolean).join(", ")})`}
                  , para {c.paragraph}
                </span>
                {c.excerpt && <span className="ds-meta block mt-1 line-clamp-2" dir="auto">{c.excerpt}</span>}
                <Link to={judgmentPath(c.docId, c.paragraph)} className="ds-link text-[15px] inline-block mt-2">
                  Read the judgment, para {c.paragraph}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

// Neutral progress wording while the answer is prepared. The backend sends no
// stage events, so the steps follow the typical timing (search ~1 s, reading,
// then writing for the rest).
const THINKING_STEPS = [
  [0, "Searching the legal library…"],
  [1500, "Reading the sources…"],
  [3500, "Writing the answer…"],
];

function Thinking() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const timers = THINKING_STEPS.slice(1).map(([ms], i) => setTimeout(() => setStep(i + 1), ms));
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div>
      <AiLabel />
      <p className="mt-4 border-t-2 border-ds-ink pt-6 flex items-center gap-3 ds-body text-ds-text-2" aria-live="polite">
        <Loader2 className="h-5 w-5 animate-spin" />
        {THINKING_STEPS[step][1]}
      </p>
    </div>
  );
}

function EmptyState({ onPick }) {
  // Live library size, so the number can't go stale after a rebuild.
  const { data: stats } = useQuery({ queryKey: ["research-stats"], queryFn: researchApi.stats, staleTime: Infinity });
  const judgments = useJudgmentsInfo();
  return (
    <div>
      <p className="ds-eyebrow">Pakistani statute law</p>
      <h2 className="ds-h2 mt-3">Ask a legal question.</h2>
      <p className="ds-body text-ds-text-2 mt-4 max-w-[640px]">
        Answers are grounded in LegalEase&apos;s library of
        {stats?.documents ? ` about ${stats.documents.toLocaleString()}` : ""} Pakistani legal documents — mostly Acts,
        Ordinances, Codes and Orders — and cite the passages they rely on.{" "}
        {judgments
          ? "Paragraphs from past judgments (a team-supplied dataset, staged) may be added as context, listed under Case law."
          : "The library holds no court judgments or case law,"}{" "}
        {judgments ? "Questions" : "and questions"} outside Pakistani law are refused.
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
