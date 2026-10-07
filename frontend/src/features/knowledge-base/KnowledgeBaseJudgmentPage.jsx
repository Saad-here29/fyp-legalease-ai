import { useEffect } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, ArrowLeft } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { ROUTES } from "@/constants";
import { kbApi } from "./api";
import { StagedTag, TopicTags } from "./JudgmentsTab";

// One judgment (kb-v2 C2): its metadata, provenance and status, and its own
// numbered paragraphs. ?para=N (linked from Research and AI Chat) scrolls to
// and marks that paragraph. Read-only; the original file is never offered.

const backTo = `${ROUTES.KNOWLEDGE_BASE}?tab=judgments`;

export default function KnowledgeBaseJudgmentPage() {
  const { source, hash } = useParams();
  const docId = `judgment/${source}/${hash}`;
  const [params] = useSearchParams();
  const para = params.get("para");

  const { data: j, isError, isFetching } = useQuery({
    queryKey: ["kb-judgment", docId],
    queryFn: () => kbApi.judgment(docId),
    retry: false,
  });

  useEffect(() => {
    if (j && para != null) document.getElementById(`para-${para}`)?.scrollIntoView({ block: "center" });
  }, [j, para]);

  return (
    <AppShell eyebrow="Knowledge Base · Judgment" title={j ? j.display_name : isError ? "Judgment not found" : "Loading…"}>
      <Link to={backTo} className="ds-link text-[15px] inline-flex items-center gap-2 mb-8">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" /> All judgments
      </Link>

      {isFetching && !j && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading the judgment…
        </p>
      )}
      {isError && (
        <p className="ds-body text-ds-text-2">
          There is no judgment with this id in the knowledge base.{" "}
          <Link to={backTo} className="ds-link">
            See all judgments
          </Link>
          .
        </p>
      )}

      {j && (
        <>
          <dl className="grid gap-x-8 sm:grid-cols-2 border-t-2 border-ds-ink">
            <Meta label="Court" value={j.court || "Not found in the heading"} />
            <Meta label="Year" value={j.year || "Not found"} />
            <Meta label="Case number" value={j.case_number || "Not found"} />
            <Meta label="Judges" value={j.judges?.length ? j.judges.join(", ") : "Not found"} />
            {j.case_name && j.case_name !== j.display_name && <Meta label="Parties (as extracted)" value={j.case_name} wide />}
            <Meta label="Topics" value={<TopicTags topics={j.topics} />} />
            <Meta
              label="Status"
              value={
                <span className="flex flex-wrap items-center gap-2">
                  <StagedTag status={j.status} />
                  {j.status !== "staged" && j.status}
                  <span className="ds-body text-ds-text-2">{j.indexed ? "In search" : "Not in search yet"}</span>
                </span>
              }
            />
            <Meta label="Provenance" value={j.provenance_note} wide />
          </dl>

          <p className="mt-8 bg-ds-sheet border border-ds-rule rounded-ds px-5 py-4 ds-body" role="note">
            Metadata was read from the judgment&apos;s first page by rules, not checked by hand. Rely on the court&apos;s own
            certified copy.
          </p>

          <section className="mt-12 max-w-[820px]" aria-labelledby="paras-heading">
            <div className="flex items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
              <h2 id="paras-heading" className="ds-h2">
                Paragraphs
              </h2>
              <p className="ds-meta">{j.paragraphs.length}</p>
            </div>
            <ol>
              {j.paragraphs.map((p, i) => {
                const active = para != null && String(p.n) === para;
                return (
                  <li
                    key={`${p.n}-${i}`}
                    id={`para-${p.n}`}
                    className={`grid grid-cols-[3.5rem_minmax(0,1fr)] gap-3 py-4 border-b border-ds-rule ${
                      active ? "bg-ds-sheet border-l-4 border-l-ds-ink pl-3" : ""
                    }`}
                    aria-current={active ? "true" : undefined}
                  >
                    <span className="ds-meta tabular-nums pt-0.5">{p.n === 0 ? "Head" : `¶ ${p.n}`}</span>
                    <p className="ds-body whitespace-pre-line break-words">{p.text}</p>
                  </li>
                );
              })}
            </ol>
          </section>
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
