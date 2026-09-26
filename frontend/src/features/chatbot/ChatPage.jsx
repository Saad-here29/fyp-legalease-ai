import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Send, Loader2, Bot, User as UserIcon, BookOpen, MessageSquarePlus } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { chatApi } from "./api";
import { cnInput } from "@/lib/formStyles";
import { renderInline } from "@/lib/markdownLite";

const SUGGESTIONS = [
  "What is the penalty for child abuse under the Zainab Alert Act?",
  "How do I file an FIR? What does Section 154 Cr.P.C. say?",
  "Explain khula under Pakistani Family Law",
  "What is murder under Section 302 of the Pakistan Penal Code?",
];

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
            role: m.sender_type === "AI" ? "assistant" : "user",
            content: m.content,
            sources: (m.citations || []).map((c) => c.source || c.title || ""),
            time: new Date(m.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
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
      return { data, elapsedMs: Math.round(performance.now() - t0) };
    },
    onSuccess: ({ data, elapsedMs }) => {
      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: data.response,
          sources: data.sources || [],
          elapsedMs,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
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
      {
        id: `me-${Date.now()}`,
        role: "user",
        content: trimmed,
        sources: [],
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setInput("");
    sendMutation.mutate({ message: trimmed, session_id: sessionId });
  };

  const startNew = () => {
    setSessionId(null);
    setMessages([]);
  };

  return (
    <AppShell title="AI legal assistant" subtitle="Pakistani law only · Every answer cites the source">
      <div className="grid gap-10 lg:grid-cols-[1fr_280px] h-[calc(100vh-220px)]">
        <div className="flex flex-col min-h-0 border-t border-hairline pt-4">
          <div ref={scrollRef} className="flex-1 overflow-y-auto pr-2 space-y-6">
            {messages.length === 0 && !sendMutation.isPending && (
              <EmptyState onPick={(q) => setInput(q)} />
            )}

            {messages.map((m) => (
              <ChatBubble key={m.id} message={m} />
            ))}

            {sendMutation.isPending && <Typing />}
          </div>

          <form
            onSubmit={submit}
            className="mt-4 flex items-end gap-3 border-t border-hairline pt-4"
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
              placeholder="Ask about Pakistani law... (English or Urdu)"
              rows={2}
              className={cnInput(false, "flex-1 resize-none py-2")}
              disabled={sendMutation.isPending}
            />
            <button
              type="submit"
              disabled={sendMutation.isPending || !input.trim()}
              className="h-10 w-10 shrink-0 bg-ink-panel text-paper hover:bg-ink-panel/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center"
              aria-label="Send"
            >
              {sendMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </form>
        </div>

        <div>
          <button
            onClick={startNew}
            className="w-full h-9 border border-hairline text-sm text-ink-text hover:border-ink-text transition-colors flex items-center justify-center gap-2 mb-8"
          >
            <MessageSquarePlus className="h-4 w-4" />
            New conversation
          </button>

          <h2 className="font-editorial text-lg text-ink-text mb-1">Recent sessions</h2>
          <div className="border-t border-hairline pt-1 mt-3">
            {!sessions || sessions.length === 0 ? (
              <p className="text-sm text-ink-muted">Your conversations will appear here.</p>
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
                      <div className="text-sm font-medium truncate">{s.title || "Untitled"}</div>
                      <div className="text-xs text-ink-muted">{s.total_messages} messages</div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ChatBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className="h-8 w-8 rounded-full bg-ink-panel/5 border border-hairline flex items-center justify-center shrink-0">
        {isUser ? (
          <UserIcon className="h-4 w-4 text-ink-muted" />
        ) : (
          <Bot className="h-4 w-4 text-ink-muted" />
        )}
      </div>
      <div className={`max-w-[min(75ch,85%)] text-sm leading-relaxed ${isUser ? "text-right" : ""}`}>
        <div
          className="whitespace-pre-wrap text-ink-text"
          dangerouslySetInnerHTML={{ __html: renderInline(message.content) }}
        />

        {!isUser && message.sources?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-hairline-subtle">
            <div className="flex items-center gap-1.5 text-xs text-ink-muted mb-1.5">
              <BookOpen className="h-3 w-3" />
              Sources
            </div>
            <ol className="text-xs text-ink-muted space-y-0.5 list-decimal list-inside">
              {message.sources.map((src, i) => (
                <li key={i}>{src}</li>
              ))}
            </ol>
          </div>
        )}

        <div className="text-xs mt-1.5 text-ink-muted/70">
          {message.time}
          {!isUser && message.elapsedMs != null && (
            <> · Generated in {(message.elapsedMs / 1000).toFixed(1)}s</>
          )}
        </div>
      </div>
    </div>
  );
}

function Typing() {
  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 rounded-full border border-hairline flex items-center justify-center shrink-0">
        <Bot className="h-4 w-4 text-ink-muted" />
      </div>
      <div className="flex items-center gap-1 py-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-ink-muted animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

function EmptyState({ onPick }) {
  return (
    <div className="flex flex-col items-center text-center py-10">
      <Bot className="h-9 w-9 text-ink-muted mb-4" />
      <h3 className="font-editorial text-2xl text-ink-text">LegalEase AI assistant</h3>
      <p className="text-ink-muted mt-2 max-w-md text-sm">
        Ask any question about Pakistani law. Answers are grounded in
        LegalEase&apos;s library of Pakistani statute text (Acts, Ordinances,
        Codes and Orders) and cite the passages they rely on — the library
        holds no court judgments or case law. Out-of-scope questions are
        politely refused.
      </p>
      <div className="mt-6 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="w-full text-left text-sm text-ink-text hover:bg-hairline-subtle/40 px-2 -mx-2 py-3 border-b border-hairline-subtle transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
      <p className="mt-6 text-xs text-ink-muted">Bilingual · English & Urdu</p>
    </div>
  );
}
