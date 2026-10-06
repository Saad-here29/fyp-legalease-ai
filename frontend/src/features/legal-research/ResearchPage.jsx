import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ROUTES } from "@/constants";
import { researchApi } from "./api";

// Legal research — design system v1, per the Research mockup
// (docs/design_reference page 11): ink search band, then ruled results.
// Adapted: the library is Pakistani statute text only, so there are no
// source-type (Judgments), jurisdiction or court filters, and no
// "Summarise top results" (not built). The query lives in the URL (?q=) so
// returning from a passage restores the results.

const EXAMPLES = ["khula procedure", "bail in a non-bailable offence", "FIR registration Section 154", "custody of minor children"];
const TOP_K = 10;
const MORE_K = 30;

// Words worth highlighting in an excerpt: the query's own words, minus
// short/common ones.
const STOP = new Set(["the", "and", "for", "with", "under", "what", "does", "from", "that", "this", "into", "section", "law"]);
const queryTerms = (q) =>
  [...new Set(q.toLowerCase().split(/[^a-z0-9]+/).filter((w) => (w.length > 3 || /^\d+$/.test(w)) && !STOP.has(w)))];

function Highlighted({ text, terms }) {
  if (!terms.length) return text;
  const re = new RegExp(`\\b(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\w*`, "gi");
  const parts = [];
  let last = 0;
  for (const m of text.matchAll(re)) {
    parts.push(text.slice(last, m.index));
    parts.push(
      <mark key={m.index} className="bg-ds-seal-tint text-ds-text rounded-ds-sm px-0.5">
        {m[0]}
      </mark>
    );
    last = m.index + m[0].length;
  }
  parts.push(text.slice(last));
  return parts;
}

export default function ResearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const k = Number(params.get("k")) || TOP_K;
  const [input, setInput] = useState(q);

  // Real corpus size from the index, so this text can't go stale after a rebuild.
  const { data: stats } = useQuery({ queryKey: ["research-stats"], queryFn: researchApi.stats, staleTime: Infinity });

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ["research", q, k],
    queryFn: () => researchApi.search({ query: q, top_k: k }),
    enabled: q.length >= 2,
    staleTime: 5 * 60 * 1000,
  });

  const run = (text, topK = TOP_K) => {
    const t = text.trim();
    if (t.length < 2) return;
    setInput(t);
    setParams(topK === TOP_K ? { q: t } : { q: t, k: String(topK) });
  };

  const terms = queryTerms(q);

  const band = (
    <>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(input);
        }}
        className="mt-6 flex flex-col sm:flex-row gap-3"
        role="search"
      >
        <label className="relative flex-1">
          <span className="sr-only">Search the statute library</span>
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-ds-text-2" aria-hidden="true" />
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. khula procedure, FIR registration, Section 302 PPC…"
            className="w-full min-h-[56px] pl-14 pr-4 rounded-ds bg-ds-sheet text-ds-text font-ds-sans text-[17px]
              placeholder:text-ds-text-2/70 focus:outline-none focus:ring-2 focus:ring-ds-paper/60"
          />
        </label>
        <button type="submit" disabled={isFetching || input.trim().length < 2} className="ds-btn-primary min-h-[56px] px-8">
          {isFetching ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Searching" /> : "Search"}
        </button>
      </form>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="font-ds-sans text-[15px] text-ds-paper/75 mr-1">Try:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => run(ex)}
            className="min-h-[40px] px-3 rounded-ds border border-ds-paper/30 font-ds-sans text-[15px] text-ds-paper/90
              hover:bg-ds-ink-2 hover:border-ds-paper/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-paper"
          >
            {ex}
          </button>
        ))}
      </div>
      <p className="mt-5 font-ds-sans text-[14px] text-ds-paper/65">
        Semantic search over Pakistani legal text — mostly Acts, Ordinances, Codes and Orders
        {stats?.chunks ? ` · ${stats.chunks.toLocaleString()} passages from about ${stats.documents.toLocaleString()} Pakistani legal documents` : ""}.
        No court judgments or case law.
      </p>
      {stats?.updates?.available && (
        <p className="mt-2 font-ds-sans text-[14px] text-ds-paper/65">
          Sources checked{" "}
          {new Date(stats.updates.last_checked).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}:{" "}
          {stats.updates.sources.map((s) => s.name).join(", ")}
          {stats.updates.new + stats.updates.changed > 0
            ? ` · ${stats.updates.new} new, ${stats.updates.changed} changed, staged for review (not yet searchable)`
            : " · no changes"}
          .
        </p>
      )}
    </>
  );

  return (
    <AppShell title="Legal research" band={band}>
      {!q && (
        <p className="ds-body text-ds-text-2 max-w-[640px]">
          Search in plain words or by section. Results are the statute passages closest in meaning to your query, most
          relevant first. Open one to read it in full, analyse it with AI or save it to a case.
        </p>
      )}

      {q && isFetching && !data && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Searching the statute library…
        </p>
      )}

      {isError && (
        <p className="flex items-start gap-2 ds-body text-ds-seal" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          {error?.response?.data?.error?.message || "Search failed. Could not reach the research service."}
        </p>
      )}

      {data && (
        <section aria-live="polite">
          <div className="flex flex-wrap items-end justify-between gap-3 pb-4 border-b-2 border-ds-ink">
            <p className="font-ds-sans text-[17px]">
              <span className="font-semibold text-[28px] leading-none tabular-nums mr-1.5">{data.results.length}</span>
              passage{data.results.length === 1 ? "" : "s"} for <span className="font-semibold">“{data.query}”</span>
            </p>
            <p className="ds-meta">Most relevant first</p>
          </div>

          {data.weak_matches && (
            <p className="mt-4 bg-ds-review-tint text-ds-review px-4 py-3 rounded-ds font-ds-sans font-semibold text-[15px] leading-[22px]" role="note">
              No strong match in the statute library. These are the closest passages and may not be relevant; try more
              specific legal terms.
            </p>
          )}
          {data.results.length === 0 ? (
            <p className="ds-body text-ds-text-2 py-8">
              No passage in the statute library is close enough to this query. Try different or more specific words.
            </p>
          ) : (
            <ul>
              {data.results.map((r) => (
                <ResultRow key={r.id} result={r} query={q} terms={terms} />
              ))}
            </ul>
          )}

          {data.results.length >= k && k < MORE_K && (
            <button onClick={() => run(q, MORE_K)} disabled={isFetching} className="ds-btn-secondary mt-8">
              {isFetching ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Loading" /> : "Show more results"}
            </button>
          )}
        </section>
      )}
    </AppShell>
  );
}

// The API's citation is often just "From: <source> (LegalEase corpus)",
// which repeats the title; show it only when it adds something (a section).
const usefulCitation = (r) => (r.citation && !/^From: .*\(LegalEase corpus\)$/.test(r.citation) ? r.citation : "");

function ResultRow({ result, query, terms }) {
  const to = ROUTES.RESEARCH_DETAIL.replace(":id", encodeURIComponent(result.id));
  const state = { result: { ...result, user_query: query } };
  const score = Math.round((result.relevance || 0) * 100);
  return (
    <li className="grid gap-x-8 gap-y-3 md:grid-cols-[minmax(0,1fr)_auto] py-6 border-b border-ds-rule">
      <div className="min-w-0">
        <p className="flex flex-wrap items-center gap-x-2 font-ds-sans text-[14px]">
          <span className="font-semibold uppercase tracking-[0.12em] text-ds-text-2">Statute</span>
          {usefulCitation(result) && <span className="text-ds-text-2">· {usefulCitation(result)}</span>}
        </p>
        <h2 className="mt-1">
          <Link
            to={to}
            state={state}
            className="font-ds-serif font-medium text-[26px] leading-[32px] text-ds-text hover:underline decoration-ds-underline decoration-2 underline-offset-4
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink rounded-ds-sm"
          >
            {result.title}
          </Link>
        </h2>
        <p className="ds-body text-ds-text-2 mt-2 line-clamp-3">
          <Highlighted text={result.excerpt} terms={terms} />
        </p>
      </div>
      <div className="flex md:flex-col md:items-end gap-x-6 gap-y-3 md:pt-6">
        <Link to={to} state={{ ...state, analyse: true }} className="ds-link text-[15px]">
          Analyse with AI
        </Link>
        <Link to={to} state={state} className="ds-link text-[15px]">
          Read passage
        </Link>
        <span className="ds-meta tabular-nums" title="Similarity between your query and this passage">
          {score}% match
        </span>
      </div>
    </li>
  );
}
