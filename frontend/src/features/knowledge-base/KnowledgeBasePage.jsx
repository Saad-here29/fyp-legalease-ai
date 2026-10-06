import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle, Search } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { Figures } from "@/features/dashboard/components/DashParts";
import { ROUTES } from "@/constants";
import { kbApi } from "./api";
import { TierTag, KbStatusTag } from "./kbParts";

// Knowledge Base — the laws the kb-v2 section records were built from, with
// their metadata, sections and records (read-only; /api/v1/kb). Ruled table
// per the Cases mockup; filters live in the URL so Back keeps them.

const FILTERS = ["q", "category", "jurisdiction", "tier", "status", "year"];

export default function KnowledgeBasePage() {
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(FILTERS.map((k) => [k, params.get(k) || ""]));
  const [q, setQ] = useState(filters.q);

  const { data: stats } = useQuery({ queryKey: ["kb-stats"], queryFn: kbApi.stats, staleTime: 5 * 60 * 1000 });
  const query = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ""));
  const { data, isFetching, isError, error } = useQuery({
    queryKey: ["kb-documents", query],
    queryFn: () => kbApi.documents(query),
    staleTime: 5 * 60 * 1000,
  });

  const set = (key, value) => {
    const next = new URLSearchParams(params);
    if (value === "" || value == null) next.delete(key);
    else next.set(key, value);
    setParams(next, { replace: true });
  };
  const anyFilter = FILTERS.some((k) => filters[k]);

  const cov = stats?.coverage;
  const categories = stats ? Object.keys(stats.by_category).filter((c) => c !== "None").sort() : [];

  return (
    <AppShell
      title="Knowledge Base"
      subtitle="The laws behind LegalEase's section-by-section library: where each record came from, its sections, and each record as stored."
    >
      <Figures
        items={[
          { label: "Laws", value: stats ? stats.laws : "–" },
          { label: "Section records", value: stats ? stats.section_records.toLocaleString() : "–" },
          {
            label: "Coverage of listed Pakistan Code Acts",
            value: cov ? `${cov.held} of ${cov.listed}` : "–",
            helper: cov ? `${cov.not_listed} more are counted by the site but not listed` : null,
          },
          {
            label: "Search passages",
            value: stats?.chunks ? stats.chunks.toLocaleString() : "–",
            helper: stats ? (stats.kb_v2_search ? "Used by Research and AI Chat" : "Not yet used by search") : null,
          },
        ]}
      />
      {cov && <p className="ds-body text-ds-text-2 mt-4 max-w-[760px]">{cov.note}</p>}

      <section className="mt-12" aria-labelledby="laws-heading">
        <div className="flex flex-wrap items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
          <h2 id="laws-heading" className="ds-h2">
            Laws
          </h2>
          <p className="ds-meta" aria-live="polite">
            {data ? `${data.total} shown` : ""}
          </p>
        </div>

        <form
          className="grid gap-4 py-6 sm:grid-cols-2 lg:grid-cols-6 border-b border-ds-rule"
          onSubmit={(e) => {
            e.preventDefault();
            set("q", q.trim());
          }}
          role="search"
        >
          <label className="sm:col-span-2 lg:col-span-2">
            <span className="ds-label">Title</span>
            <span className="relative block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-ds-text-2" aria-hidden="true" />
              <input
                className="ds-input pl-10"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onBlur={() => q.trim() !== filters.q && set("q", q.trim())}
                placeholder="e.g. guardians, penal"
              />
            </span>
          </label>
          <Select label="Category" value={filters.category} onChange={(v) => set("category", v)}
            options={[["", "All"], ...categories.map((c) => [c, c])]} />
          <Select label="Jurisdiction" value={filters.jurisdiction} onChange={(v) => set("jurisdiction", v)}
            options={[["", "All"], ...(stats?.jurisdictions || []).map((j) => [j, j])]} />
          <Select label="Source tier" value={filters.tier} onChange={(v) => set("tier", v)}
            options={[["", "All"], ["1", "Tier 1"], ["2", "Tier 2"]]} />
          <Select label="Status" value={filters.status} onChange={(v) => set("status", v)}
            options={[["", "All"], ["current", "Current"], ["under_review", "Under review"], ["repealed", "Repealed"]]} />
          <label className="lg:col-span-1">
            <span className="ds-label">Year</span>
            <input
              className="ds-input"
              inputMode="numeric"
              value={filters.year}
              onChange={(e) => set("year", e.target.value.replace(/\D/g, "").slice(0, 4))}
              placeholder="e.g. 1890"
            />
          </label>
          <div className="flex items-end gap-3 sm:col-span-2 lg:col-span-5">
            <button type="submit" className="ds-btn-secondary">Apply</button>
            {anyFilter && (
              <button
                type="button"
                className="ds-link text-[15px] min-h-[44px]"
                onClick={() => {
                  setQ("");
                  setParams({}, { replace: true });
                }}
              >
                Clear filters
              </button>
            )}
          </div>
        </form>

        {isFetching && !data && (
          <p className="flex items-center gap-3 ds-body text-ds-text-2 py-6">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading the knowledge base…
          </p>
        )}
        {isError && (
          <p className="flex items-start gap-2 ds-body text-ds-seal py-6" role="alert">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            {error?.response?.data?.error?.message || "Could not load the knowledge base."}
          </p>
        )}
        {data && data.documents.length === 0 && (
          <p className="ds-body text-ds-text-2 py-8">No law matches these filters.</p>
        )}
        {data && data.documents.length > 0 && <LawTable laws={data.documents} />}
      </section>
    </AppShell>
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

const lawPath = (id) => ROUTES.KNOWLEDGE_BASE_LAW.replace(":id", encodeURIComponent(id));

function LawTable({ laws }) {
  return (
    <>
      {/* Desktop: a ruled table. */}
      <table className="hidden md:table w-full text-left">
        <thead>
          <tr className="border-b border-ds-rule">
            {["Title", "Category", "Jurisdiction", "Year", "Tier", "Status", "Sections"].map((h) => (
              <th key={h} scope="col" className={`ds-meta py-3 pr-4 ${h === "Year" || h === "Sections" ? "text-right" : ""}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {laws.map((l) => (
            <tr key={l.doc_id} className="border-b border-ds-rule align-middle">
              <td className="py-4 pr-4">
                <Link to={lawPath(l.doc_id)} className="ds-link text-[17px] leading-[24px]">
                  {l.title}
                </Link>
                {l.audience && l.audience !== "general" && (
                  <span className="block ds-meta mt-1">For: {l.audience}</span>
                )}
              </td>
              <td className="py-4 pr-4 ds-body text-ds-text-2">{l.category || "—"}</td>
              <td className="py-4 pr-4 ds-body text-ds-text-2">{l.jurisdiction}</td>
              <td className="py-4 pr-4 ds-body text-ds-text-2 text-right tabular-nums">{l.year}</td>
              <td className="py-4 pr-4"><TierTag tier={l.source_tier} /></td>
              <td className="py-4 pr-4">{l.status === "current" ? <span className="ds-body text-ds-text-2">Current</span> : <KbStatusTag status={l.status} />}</td>
              <td className="py-4 ds-body text-right tabular-nums">{l.sections}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Phone: ruled rows. */}
      <ul className="md:hidden">
        {laws.map((l) => (
          <li key={l.doc_id} className="py-5 border-b border-ds-rule">
            <Link to={lawPath(l.doc_id)} className="ds-link text-[18px] leading-[26px]">
              {l.title}
            </Link>
            <p className="ds-body text-ds-text-2 mt-1">
              {[l.category || "No category", l.jurisdiction, l.year, `${l.sections} section${l.sections === 1 ? "" : "s"}`].join(" · ")}
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              <TierTag tier={l.source_tier} />
              <KbStatusTag status={l.status} />
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
