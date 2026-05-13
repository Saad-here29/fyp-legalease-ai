import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  Send,
  Loader2,
  Bot,
  User as UserIcon,
  Sparkles,
  BookOpen,
  MessageSquarePlus,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { chatApi } from "./api";

const SUGGESTIONS = [
  "What is the penalty for child abuse under the Zainab Alert Act?",
  "How do I file an FIR? What does Section 154 Cr.P.C. say?",
  "Explain khula under Pakistani Family Law",
  "What is murder under Section 302 of the Pakistan Penal Code?",
];

// Tiny markdown — bold via **text**, newlines preserved. Safe-ish because
// we render onto a <span> after escaping the original.
function renderInline(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}

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
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: async (payload) => {
      // Track client-side latency so the AI bubble can show "Generated in Xs"
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
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    onError: (err) => {
      const apiErr = err?.response?.data?.error;
      toast.error(apiErr?.message || "AI is unavailable right now.", {
        description: apiErr?.hint,
      });
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
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
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
    <DashboardLayout
      title="AI Legal Assistant"
      subtitle="Pakistani law only · Every answer cites the source"
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <PanelCard className="flex flex-col h-[calc(100vh-220px)]">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto scrollbar-thin pr-2 space-y-4"
          >
            {messages.length === 0 && !sendMutation.isPending && (
              <EmptyState onPick={(q) => setInput(q)} />
            )}

            <AnimatePresence>
              {messages.map((m) => (
                <ChatBubble key={m.id} message={m} />
              ))}
            </AnimatePresence>

            {sendMutation.isPending && <Typing />}
          </div>

          <form
            onSubmit={submit}
            className="mt-4 flex items-end gap-2 border-t border-border/40 pt-4"
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
              className="flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm"
              disabled={sendMutation.isPending}
            />
            <Button
              type="submit"
              variant="gold"
              size="lg"
              disabled={sendMutation.isPending || !input.trim()}
            >
              {sendMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </PanelCard>

        <div className="space-y-4">
          <Button onClick={startNew} variant="outline" className="w-full">
            <MessageSquarePlus className="h-4 w-4" />
            New conversation
          </Button>
          <PanelCard title="Recent sessions">
            {!sessions || sessions.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Your conversations will appear here.
              </p>
            ) : (
              <ul className="space-y-2">
                {sessions.slice(0, 8).map((s) => (
                  <li key={s.id}>
                    <button
                      onClick={() => setSessionId(s.id)}
                      className={`w-full text-left text-sm rounded-md px-3 py-2 transition-colors ${
                        sessionId === s.id
                          ? "bg-accent/15 text-accent"
                          : "hover:bg-secondary/40 text-foreground"
                      }`}
                    >
                      <div className="truncate font-medium">
                        {s.title || "Untitled"}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {s.total_messages} messages
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </PanelCard>
        </div>
      </div>
    </DashboardLayout>
  );
}

function ChatBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser ? "bg-accent/15" : "bg-legal-gold/15"
        }`}
      >
        {isUser ? (
          <UserIcon className="h-4 w-4 text-accent" />
        ) : (
          <Bot className="h-4 w-4 text-legal-gold" />
        )}
      </div>
      <div
        className={`max-w-[min(75ch,85%)] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-accent/15 border border-accent/30 rounded-tr-sm"
            : "bg-card/70 border border-border/40 rounded-tl-sm"
        }`}
      >
        <div
          className="whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ __html: renderInline(message.content) }}
        />

        {!isUser && message.sources?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/40">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              <BookOpen className="h-3 w-3" />
              Sources
            </div>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.map((src, i) => (
                <Badge key={i} variant="gold" className="text-[10px]">
                  {src}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="text-[10px] mt-2 text-muted-foreground flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span>{message.time}</span>
          {!isUser && message.elapsedMs != null && (
            <>
              <span>·</span>
              <span>
                Generated in {(message.elapsedMs / 1000).toFixed(1)}s
              </span>
            </>
          )}
          {!isUser && message.sources?.length > 0 && (
            <>
              <span>·</span>
              <span>
                {message.sources.length} source
                {message.sources.length === 1 ? "" : "s"}
              </span>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function Typing() {
  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 rounded-full bg-legal-gold/15 flex items-center justify-center">
        <Bot className="h-4 w-4 text-legal-gold" />
      </div>
      <div className="bg-card/70 border border-border/40 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-legal-gold animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

function EmptyState({ onPick }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12">
      <div className="h-16 w-16 rounded-2xl bg-gold-gradient flex items-center justify-center mb-4">
        <Bot className="h-8 w-8 text-legal-navy" />
      </div>
      <h3 className="font-serif text-2xl font-bold gold-text">
        LegalEase AI Assistant
      </h3>
      <p className="text-muted-foreground mt-2 max-w-md text-sm">
        Ask any question about Pakistani law. I'll cite the source statute
        or judgment for every answer. Out-of-scope questions are politely
        refused.
      </p>
      <div className="mt-6 grid gap-2 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="text-left text-sm rounded-lg border border-border/40 bg-card/30 px-4 py-3 hover:border-accent/40 hover:bg-accent/5 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
      <Badge variant="gold" className="mt-6">
        <Sparkles className="h-3 w-3 mr-1" />
        Bilingual · English & Urdu
      </Badge>
    </div>
  );
}
