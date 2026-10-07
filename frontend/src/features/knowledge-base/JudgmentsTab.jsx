import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Loader2, AlertCircle, Search } from "lucide-react";
import { kbApi } from "./api";
import { judgmentPath } from "./kbFormat";

// Knowledge Base "Judgments" tab (kb-v2 C2): the team-supplied judgments,
// one row per case (copies in two datasets shown once), read from the
// records files. Filters live in the URL (?tab=judgments&jq=&jcourt=…).

const PAGE_SIZE = 25;
const KEYS = { q: "jq", court: "jcourt", year: "jyear", topic: "jtopic", page: "jpage" };

export function TopicTags({ topics }) {
  if (!topics?.length) return <span className="ds-body text-ds-text-2">—</span>;
  return (
    <span className="flex flex-wrap gap-1.5">
      {topics.map((t) => (
        <span key={t} className="ds-tag-neutral whitespace-nowrap">
          {t}
        </span>
      ))}
    </span>
  );
}

export function StagedTag({ status }) {
  if (status !== "staged") return null;
  return (
    <span className="ds-tag-review whitespace-nowrap" title="Staged: not yet reviewed by the team">
      ! Staged, not yet reviewed
    </span>
  );
}

export default function JudgmentsTab({ info }) {
  const [params, setParams] = useSearchParams();
  const f = Object.fromEntries(Object.entries(KEYS).map(([k, key]) => [k, params.get(key) || ""]));
  const [q, setQ] = useState(f.q);
  const page = Number(f.page) || 1;

  const query = {
    ...(f.q && { q: f.q }),
    ...(f.court && { court: f.court }),
    ...(f.year && { year: Number(f.year) }),
    ...(f.topic && { topic: f.topic }),
    page,
    page_size: PAGE_SIZE,
  };
  const { data, isFetching, isError, error } = useQuery({
    queryKey: ["kb-judgments", query],
    queryFn: () => kbApi.judgments(query),
    staleTime: 5 * 60 * 1000,
    placeholderData: keepPreviousData,
  });

  const set = (key, value) => {
    const next = new URLSearchParams(params);
    if (value === "" || value == null) next.delete(KEYS[key]);
    else next.set(KEYS[key], value);
    if (key !== "page") next.delete(KEYS.page);
    setParams(next, { replace: true });
  };
  const anyFilter = ["q", "court", "year", "topic"].some((k) => f[k]);
  const courts = Object.keys(info?.courts || {}).filter((c) => c !== "Unknown");
  const topics = Object.keys(info?.topics || {});
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <section className="mt-12" aria-labelledby="judgments-heading">
      <div className="flex flex-wrap items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
        <h2 id="judgments-heading" className="ds-h2">
          Judgments
        </h2>
        <p className="ds-meta" aria-live="polite">
          {data ? `${data.total.toLocaleString()} shown · ${data.counts.indexed.toLocaleString()} in search` : ""}
        </p>
      </div>
      <p className="ds-body text-ds-text-2 mt-4 max-w-[760px]">
        Dataset supplied by the team; original source and licence to be confirmed. Judgments are staged, not yet
        reviewed. Near-empty files, duplicates and publishers&apos; law-report copies are left out.
      </p>

      <form
        className="grid gap-4 py-6 sm:grid-cols-2 lg:grid-cols-6 border-b border-ds-rule"
        onSubmit={(e) => {
          e.preventDefault();
          set("q", q.trim());
        }}
        role="search"
      >
        <label className="sm:col-span-2 lg:col-span-3">
          <span className="ds-label">Name, case number or judge</span>
          <span className="relative block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-ds-text-2" aria-hidden="true" />
            <input
              className="ds-input pl-10"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onBlur={() => q.trim() !== f.q && set("q", q.trim())}
              placeholder="e.g. Saima Khan, 3718"
            />
          </span>
        </label>
        <Select label="Court" value={f.court} onChange={(v) => set("court", v)} options={[["", "All courts"], ...courts.map((c) => [c, c])]} />
        <Select label="Topic" value={f.topic} onChange={(v) => set("topic", v)} options={[["", "All topics"], ...topics.map((t) => [t, t])]} />
        <label>
          <span className="ds-label">Year</span>
          <input
            className="ds-input"
            inputMode="numeric"
            value={f.year}
            onChange={(e) => {
              const y = e.target.value.replace(/\D/g, "").slice(0, 4);
              if (y.length === 4 || y === "") set("year", y);
            }}
            placeholder="e.g. 2023"
          />
        </label>
        <div className="flex items-end gap-3 sm:col-span-2 lg:col-span-6">
          <button type="submit" className="ds-btn-secondary">Apply</button>
          {anyFilter && (
            <button
              type="button"
              className="ds-link text-[15px] min-h-[44px]"
              onClick={() => {
                setQ("");
                const next = new URLSearchParams(params);
                Object.values(KEYS).forEach((k) => next.delete(k));
                setParams(next, { replace: true });
              }}
            >
              Clear filters
            </button>
          )}
        </div>
      </form>

      {isFetching && !data && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2 py-6">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading judgments…
        </p>
      )}
      {isError && (
        <p className="flex items-start gap-2 ds-body text-ds-seal py-6" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          {error?.response?.data?.error?.message || "Could not load the judgments."}
        </p>
      )}
      {data && data.judgments.length === 0 && <p className="ds-body text-ds-text-2 py-8">No judgment matches these filters.</p>}
      {data && data.judgments.length > 0 && <JudgmentTable rows={data.judgments} />}

      {data && pages > 1 && (
        <nav className="flex items-center gap-4 mt-6" aria-label="Pages">
          <button className="ds-btn-secondary" disabled={page <= 1} onClick={() => set("page", String(page - 1))}>
            Previous
          </button>
          <span className="ds-meta tabular-nums">
            Page {page} of {pages}
          </span>
          <button className="ds-btn-secondary" disabled={page >= pages} onClick={() => set("page", String(page + 1))}>
            Next
          </button>
        </nav>
      )}
    </section>
  );
}

function Select({ label, value, onChange, options }) {
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

function JudgmentTable({ rows }) {
  return (
    <>
      {/* Desktop: a ruled table. */}
      <table className="hidden md:table w-full text-left">
        <thead>
          <tr className="border-b border-ds-rule">
            {["Judgment", "Court", "Year", "Case number", "Topics"].map((h) => (
              <th key={h} scope="col" className={`ds-meta py-3 pr-4 ${h === "Year" ? "text-right" : ""}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((j) => (
            <tr key={j.doc_id} className="border-b border-ds-rule align-top">
              <td className="py-4 pr-4 max-w-[380px]">
                <Link to={judgmentPath(j.doc_id)} className="ds-link text-[17px] leading-[24px]">
                  {j.display_name}
                </Link>
                {!j.indexed && <span className="block ds-meta mt-1">Not in search yet</span>}
              </td>
              <td className="py-4 pr-4 ds-body text-ds-text-2">{j.court || "—"}</td>
              <td className="py-4 pr-4 ds-body text-ds-text-2 text-right tabular-nums">{j.year || "—"}</td>
              <td className="py-4 pr-4 ds-body text-ds-text-2">{j.case_number || "—"}</td>
              <td className="py-4">
                <TopicTags topics={j.topics} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Phone: ruled rows. */}
      <ul className="md:hidden">
        {rows.map((j) => (
          <li key={j.doc_id} className="py-5 border-b border-ds-rule">
            <Link to={judgmentPath(j.doc_id)} className="ds-link text-[18px] leading-[26px]">
              {j.display_name}
            </Link>
            <p className="ds-body text-ds-text-2 mt-1">{[j.court, j.year, j.case_number].filter(Boolean).join(" · ")}</p>
            <div className="mt-2">
              <TopicTags topics={j.topics} />
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
