import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle, ArrowLeft, Copy, Check } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ROUTES } from "@/constants";
import { kbApi, saveBlob, openBlob } from "./api";
import { TierTag, KbStatusTag } from "./kbParts";
import { sectionLabel } from "./kbFormat";

// One law in the knowledge base: its metadata and provenance, the Pakistan
// Code notice, its section records, and the selected record as stored
// (?record=<id>, so a record can be linked from Research and AI Chat).

const NOTICE =
  "Content on Pakistan Code is under review; the Gazette is authoritative. LegalEase shows source and fetch details for every record.";

export default function KnowledgeBaseLawPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const recordId = params.get("record");
  const [busy, setBusy] = useState("");
  const [actionError, setActionError] = useState("");

  const law = useQuery({ queryKey: ["kb-law", id], queryFn: () => kbApi.document(id) });
  const secs = useQuery({ queryKey: ["kb-sections", id], queryFn: () => kbApi.sections(id) });

  const run = async (what, fn) => {
    setBusy(what);
    setActionError("");
    try {
      await fn();
    } catch (e) {
      setActionError(e?.response?.status === 404 ? "No saved original for this law." : "That didn't work. Try again.");
    } finally {
      setBusy("");
    }
  };

  const l = law.data;
  return (
    <AppShell
      eyebrow="Knowledge Base"
      title={l ? l.title : law.isError ? "Law not found" : "Loading…"}
      headerActions={
        l && (
          <>
            {l.has_original && (
              <button
                className="ds-btn-secondary"
                disabled={!!busy}
                onClick={() => run("original", async () => openBlob(await kbApi.original(id)))}
              >
                {busy === "original" ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Opening" /> : "Open original"}
              </button>
            )}
            <button
              className="ds-btn-primary"
              disabled={!!busy}
              onClick={() => run("json", async () => saveBlob(await kbApi.downloadJson(id), `${id}.json`))}
            >
              {busy === "json" ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Downloading" /> : "Download JSON"}
            </button>
          </>
        )
      }
    >
      <Link to={ROUTES.KNOWLEDGE_BASE} className="ds-link text-[15px] inline-flex items-center gap-2 mb-8">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" /> All laws
      </Link>

      {actionError && (
        <p className="flex items-start gap-2 ds-body text-ds-seal mb-6" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" /> {actionError}
        </p>
      )}
      {law.isError && (
        <p className="ds-body text-ds-text-2">
          There is no law with this id in the knowledge base. <Link to={ROUTES.KNOWLEDGE_BASE} className="ds-link">See all laws</Link>.
        </p>
      )}

      {l && (
        <>
          <dl className="grid gap-x-8 sm:grid-cols-2 border-t-2 border-ds-ink">
            <Meta
              label="Category"
              value={
                !l.category
                  ? "Not in a Pakistan Code category listing"
                  : l.category_source === "LegalEase override"
                    ? `${l.category} (assigned by LegalEase; not in a Pakistan Code category listing)`
                    : l.category
              }
            />
            <Meta label="Jurisdiction" value={l.jurisdiction} />
            <Meta label="Year" value={l.year} />
            <Meta label="Act number" value={l.act_number || "Not recorded"} />
            <Meta label="Source" value={l.source_label} />
            <Meta label="Source tier" value={<TierTag tier={l.source_tier} />} />
            <Meta label="Status" value={l.status === "current" ? "Current" : <KbStatusTag status={l.status} />} />
            <Meta label="Applies to" value={l.audience === "general" ? "General" : l.audience} />
            {l.source_version && <Meta label="Version in the file" value={l.source_version} wide />}
            <Meta label="Source URL" value={l.source_url ? <a className="ds-link" href={l.source_url} target="_blank" rel="noopener noreferrer">{l.source_url}</a> : "Not recorded"} wide />
            {l.provenance_note && <Meta label="Provenance" value={l.provenance_note} wide />}
          </dl>

          <p className="mt-8 bg-ds-sheet border border-ds-rule rounded-ds px-5 py-4 ds-body" role="note">
            {NOTICE}
          </p>

          <div className="mt-12 grid gap-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
            <Sections
              data={secs.data}
              loading={secs.isFetching && !secs.data}
              selected={recordId}
              onSelect={(rid) => setParams({ record: rid }, { replace: false })}
              sectioned={l.sectioned}
            />
            <RecordPanel recordId={recordId} />
          </div>
        </>
      )}
    </AppShell>
  );
}

function Meta({ label, value, wide = false }) {
  return (
    <div className={`py-4 border-b border-ds-rule ${wide ? "sm:col-span-2" : ""}`}>
      <dt className="ds-meta">{label}</dt>
      <dd className="ds-body mt-1 break-words">{value}</dd>
    </div>
  );
}

function Sections({ data, loading, selected, onSelect, sectioned }) {
  return (
    <section aria-labelledby="sections-heading">
      <div className="flex items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
        <h2 id="sections-heading" className="ds-h2">
          {sectioned ? "Sections" : "Passages"}
        </h2>
        {data && <p className="ds-meta">{data.sections.length}</p>}
      </div>
      {!sectioned && (
        <p className="ds-body text-ds-text-2 mt-4">
          This law could not be split reliably into sections, so it is stored as numbered passages.
        </p>
      )}
      {loading && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2 py-6">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading sections…
        </p>
      )}
      {data && (
        <ol className="lg:max-h-[960px] lg:overflow-y-auto">
          {data.sections.map((s, i) => {
            const active = s.id === selected;
            return (
              <li key={s.id} className="border-b border-ds-rule">
                <button
                  onClick={() => onSelect(s.id)}
                  aria-current={active ? "true" : undefined}
                  className={`w-full text-left py-4 px-3 min-h-[56px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink ${
                    active ? "bg-ds-sheet border-l-4 border-ds-ink" : "hover:bg-ds-sheet/60"
                  }`}
                >
                  <span className="block font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text">
                    {sectionLabel(s.section, s.heading) || `Passage ${i + 1}`}
                  </span>
                  <span className="block ds-body text-ds-text-2 mt-1 line-clamp-2">{s.preview}</span>
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

function RecordPanel({ recordId }) {
  const ref = useRef(null);
  const [copied, setCopied] = useState(false);
  const rec = useQuery({
    queryKey: ["kb-record", recordId],
    queryFn: () => kbApi.record(recordId),
    enabled: !!recordId,
  });
  const json = rec.data ? JSON.stringify(rec.data, null, 2) : "";

  useEffect(() => {
    // On a phone the record sits below the section list: bring it into view.
    if (rec.data && ref.current && window.innerWidth < 1024) ref.current.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [rec.data]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section ref={ref} aria-labelledby="record-heading" className="min-w-0 scroll-mt-20">
      <div className="flex items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
        <h2 id="record-heading" className="ds-h2">
          Record
        </h2>
        {rec.data && (
          <button onClick={copy} className="ds-btn-secondary min-h-[44px]">
            {copied ? <Check className="h-5 w-5" aria-hidden="true" /> : <Copy className="h-5 w-5" aria-hidden="true" />}
            {copied ? "Copied" : "Copy"}
          </button>
        )}
      </div>
      {!recordId && <p className="ds-body text-ds-text-2 py-6">Choose a section to see its record exactly as stored, in JSON.</p>}
      {rec.isFetching && !rec.data && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2 py-6">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading the record…
        </p>
      )}
      {rec.isError && <p className="ds-body text-ds-seal py-6" role="alert">This record could not be found.</p>}
      {rec.data && (
        <pre
          className="mt-4 bg-ds-sheet border border-ds-rule rounded-ds p-4 overflow-x-auto font-mono text-[14px] leading-[22px] text-ds-text whitespace-pre-wrap break-words"
          aria-label="Record JSON"
        >
          {json}
        </pre>
      )}
    </section>
  );
}
