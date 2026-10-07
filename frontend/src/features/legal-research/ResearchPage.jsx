import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ROUTES } from "@/constants";
import { researchApi } from "./api";
import { kbApi } from "@/features/knowledge-base/api";
import { TierTag, KbSourceLink } from "@/features/knowledge-base/kbParts";
import { sectionLabel } from "@/features/knowledge-base/kbFormat";

// Legal research — design system v1, per the Research mockup
// (docs/design_reference page 11): ink search band, then ruled results.
// Adapted: the library is Pakistani statute text only, so there are no
// source-type (Judgments) or court filters, and no "Summarise top results"
// (not built). Category, jurisdiction, source tier and year filters (kb-v2)
// apply only to passages whose law's metadata is known; the page says how
// many documents that covers. Query and filters live in the URL (?q=&cat=…)
// so returning from a passage restores the results.

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
  const filters = {
    category: params.get("cat") || "",
    jurisdiction: params.get("jur") || "",
    source_tier: params.get("tier") || "",
    year_from: params.get("yf") || "",
    year_to: params.get("yt") || "",
  };
  const activeFilters = Object.fromEntries(
    Object.entries(filters)
      .filter(([, v]) => v !== "")
      .map(([key, v]) => [key, ["source_tier", "year_from", "year_to"].includes(key) ? Number(v) : v])
  );
  const setFilter = (key, value) => {
    const next = new URLSearchParams(params);
    if (value === "") next.delete(key);
    else next.set(key, value);
    next.delete("k");
    setParams(next, { replace: true });
  };
  const clearFilters = () => {
    const next = new URLSearchParams(params);
    ["cat", "jur", "tier", "yf", "yt"].forEach((key) => next.delete(key));
    setParams(next, { replace: true });
  };
  const { data: kbStats } = useQuery({ queryKey: ["kb-stats"], queryFn: kbApi.stats, staleTime: 5 * 60 * 1000 });

  // Real corpus size from the index, so this text can't go stale after a rebuild.
  const { data: stats } = useQuery({ queryKey: ["research-stats"], queryFn: researchApi.stats, staleTime: Infinity });

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ["research", q, k, activeFilters],
    queryFn: () => researchApi.search({ query: q, top_k: k, ...activeFilters }),
    enabled: q.length >= 2,
    staleTime: 5 * 60 * 1000,
  });

  const run = (text, topK = TOP_K) => {
    const t = text.trim();
    if (t.length < 2) return;
    setInput(t);
    const next = new URLSearchParams(params);
    next.set("q", t);
    if (topK === TOP_K) next.delete("k");
    else next.set("k", String(topK));
    setParams(next);
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
            : " · no changes in the latest check"}
          {stats.updates.last_updated &&
            ` · last update found ${new Date(stats.updates.last_updated).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}`}
          .
        </p>
      )}
    </>
  );

  return (
    <AppShell title="Legal research" band={band}>
      <FilterBar
        key={`${filters.year_from}-${filters.year_to}`}
        filters={filters}
        setFilter={setFilter}
        clearFilters={clearFilters}
        categories={kbStats?.categories || []}
        jurisdictions={kbStats?.jurisdictions || ["Pakistan"]}
        coverage={stats?.filter_coverage}
      />
      {!q && (
        <p className="ds-body text-ds-text-2 max-w-[640px]">
          Search in plain words or by section. Results are the statute passages closest in meaning to your query, most
          relevant first. Open one to read it in full, analyse it with AI or save it to a case.
        </p>
      )}

      {q && isFetching && !data && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Searching the legal library…
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
          {data.results.length === 0 && data.filters_active ? (
            <div className="py-8">
              <p className="ds-body text-ds-text-2">No passage matches this query with these filters.</p>
              <button onClick={clearFilters} className="ds-btn-secondary mt-4">
                Clear filters
              </button>
            </div>
          ) : data.results.length === 0 ? (
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
        <p className="flex flex-wrap items-center gap-x-2 gap-y-2 font-ds-sans text-[14px]">
          <span className="font-semibold uppercase tracking-[0.12em] text-ds-text-2">Statute</span>
          {usefulCitation(result) && <span className="text-ds-text-2">· {usefulCitation(result)}</span>}
          {(result.category || result.year) && (
            <span className="text-ds-text-2">· {[result.category, result.year].filter(Boolean).join(", ")}</span>
          )}
          <TierTag tier={result.source_tier} />
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
        {(result.section || result.heading) && (
          <p className="font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text mt-1">
            {sectionLabel(result.section, result.heading)}
          </p>
        )}
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
        <KbSourceLink sourceUrl={result.source_url} recordId={result.kb_record_id} />
        <span className="ds-meta tabular-nums" title="Similarity between your query and this passage">
          {score}% match
        </span>
      </div>
    </li>
  );
}

function FilterBar({ filters, setFilter, clearFilters, categories, jurisdictions, coverage }) {
  const [yf, setYf] = useState(filters.year_from);
  const [yt, setYt] = useState(filters.year_to);
  const any = Object.values(filters).some((v) => v !== "");
  const year = (v) => v.replace(/\D/g, "").slice(0, 4);
  const commit = (key, v) => setFilter(key, v.length === 4 ? v : "");
  return (
    <section aria-label="Filters" className="mb-10 pb-6 border-b border-ds-rule">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <FilterSelect
          label="Category"
          value={filters.category}
          onChange={(v) => setFilter("cat", v)}
          options={[["", "All categories"], ...categories.map((c) => [c, c])]}
        />
        <FilterSelect
          label="Jurisdiction"
          value={filters.jurisdiction}
          onChange={(v) => setFilter("jur", v)}
          options={[["", "All"], ...jurisdictions.map((j) => [j, j])]}
        />
        <FilterSelect
          label="Source tier"
          value={filters.source_tier}
          onChange={(v) => setFilter("tier", v)}
          options={[["", "All tiers"], ["1", "Tier 1"], ["2", "Tier 2"]]}
        />
        <label>
          <span className="ds-label">Year from</span>
          <input
            className="ds-input"
            inputMode="numeric"
            placeholder="e.g. 1860"
            value={yf}
            onChange={(e) => setYf(year(e.target.value))}
            onBlur={() => commit("yf", yf)}
            onKeyDown={(e) => e.key === "Enter" && commit("yf", yf)}
          />
        </label>
        <label>
          <span className="ds-label">Year to</span>
          <input
            className="ds-input"
            inputMode="numeric"
            placeholder="e.g. 1990"
            value={yt}
            onChange={(e) => setYt(year(e.target.value))}
            onBlur={() => commit("yt", yt)}
            onKeyDown={(e) => e.key === "Enter" && commit("yt", yt)}
          />
        </label>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2">
        {coverage && (
          <p className="ds-body text-ds-text-2">
            Filters cover laws with known metadata ({coverage.known.toLocaleString()} of {coverage.total.toLocaleString()}).
          </p>
        )}
        {any && (
          <button type="button" onClick={clearFilters} className="ds-link text-[15px] min-h-[44px]">
            Clear filters
          </button>
        )}
      </div>
    </section>
  );
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label>
      <span className="ds-label">{label}</span>
      <select className="ds-input pr-8" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, t]) => (
          <option key={v} value={v}>
            {t}
          </option>
        ))}
      </select>
    </label>
  );
}
