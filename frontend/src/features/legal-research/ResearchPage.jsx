import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Search, Loader2, BookOpen, ArrowRight, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import { ROUTES } from "@/constants";
import { researchApi } from "./api";

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  // Real corpus size from the index, so this text can't go stale after a
  // rebuild (it once said 88,036 long after the index had changed).
  const { data: stats } = useQuery({
    queryKey: ["research-stats"],
    queryFn: researchApi.stats,
    staleTime: Infinity,
  });

  const { mutate, data, isPending, isError, error, reset } = useMutation({
    mutationFn: (payload) => researchApi.search(payload),
  });

  const submit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    reset();
    mutate({
      query: query.trim(),
      top_k: 10,
    });
  };

  return (
    <AppShell
      title="AI legal research"
      subtitle="Semantic search over Pakistani statute text — Acts, Ordinances, Codes and Orders"
    >
      <form onSubmit={submit} className="pb-8 mb-8 border-b border-hairline space-y-5">
        <div className="flex items-end gap-3">
          <div className="flex-1 flex items-center gap-2 border-b border-hairline focus-within:border-ink-text focus-within:bg-ink-text/[0.03] px-1 -mx-1 pb-1.5 transition-colors">
            <Search className="h-4 w-4 text-ink-muted" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. khula procedure, FIR registration, child custody, Section 302 PPC..."
              className="flex-1 bg-transparent outline-none text-sm text-ink-text placeholder:text-ink-muted/60"
            />
          </div>
          <AppButton type="submit" disabled={isPending || !query.trim()} className="shrink-0">
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
          </AppButton>
        </div>
      </form>

      {isPending && (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-ink-muted mb-4">
            <Loader2 className="h-3 w-3 animate-spin" />
            {stats?.chunks
              ? `Searching ${stats.chunks.toLocaleString()} passages from ${stats.documents.toLocaleString()} statute documents…`
              : "Searching the statute library…"}
          </div>
          {[0, 1, 2].map((i) => (
            <div key={i} className="py-4 border-b border-hairline-subtle animate-pulse">
              <div className="h-3 w-24 bg-hairline-subtle mb-2" />
              <div className="h-4 w-3/4 bg-hairline-subtle" />
            </div>
          ))}
        </div>
      )}

      {isError && (
        <div className="flex items-start gap-3 py-2">
          <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-ink-text">Search failed.</p>
            <p className="text-ink-muted mt-1">
              {error?.response?.data?.error?.message ||
                "Could not reach the research service. Is the backend running?"}
            </p>
          </div>
        </div>
      )}

      {data && data.results.length === 0 && !isPending && (
        <p className="text-sm text-ink-muted text-center py-8">
          No matching authorities found. Try different or more specific
          keywords.
        </p>
      )}

      {data && data.results.length > 0 && (
        <div>
          <p className="text-sm text-ink-muted mb-2">
            {data.total} result{data.total === 1 ? "" : "s"} for{" "}
            <span className="text-ink-text font-medium">"{data.query}"</span>
          </p>
          <ul>
            {data.results.map((r) => (
              <ResultRow key={r.id} result={r} />
            ))}
          </ul>
        </div>
      )}
    </AppShell>
  );
}

function ResultRow({ result }) {
  const score = Math.round((result.relevance || 0) * 100);
  return (
    <li className="py-5 border-b border-hairline-subtle last:border-0">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1 text-xs text-ink-muted">
            <BookOpen className="h-3.5 w-3.5" />
            <span>{result.case_type === "judgment" ? "Judgment" : "Statute"}</span>
            {result.year && <span>· {result.year}</span>}
            {result.court && <span>· {result.court}</span>}
          </div>
          <h3 className="font-editorial text-lg text-ink-text leading-tight">{result.title}</h3>
          {result.citation && (
            <p className="text-xs text-ink-muted mt-0.5">{result.citation}</p>
          )}
        </div>
        <span className="text-xs text-ink-muted shrink-0">{score}% match</span>
      </div>

      <p className="mt-2 text-sm text-ink-muted leading-relaxed line-clamp-3">
        {result.excerpt}
      </p>

      <div className="mt-2">
        <Link
          to={ROUTES.RESEARCH_DETAIL.replace(":id", encodeURIComponent(result.id))}
          state={{ result }}
          className="inline-flex items-center gap-1 text-sm text-brick hover:underline underline-offset-2"
        >
          Read more <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </li>
  );
}
