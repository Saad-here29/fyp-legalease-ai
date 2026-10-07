import { useState } from "react";
import { AlertCircle, AlertTriangle } from "lucide-react";
import Markdown from "@/lib/Markdown";
import ReasoningPanel from "./ReasoningPanel";

// Display names for the NER model's entity types (backend app/ai/ner.py).
const ENTITY_LABELS = {
  per: "People",
  org: "Organisations",
  resp: "Respondents",
  date: "Dates",
  loc: "Places",
  money: "Amounts",
  caseno: "Case numbers",
  appealcaseno: "Case appealed from",
  appealcourt: "Court appealed from",
  refcase: "Cited cases",
  refcourt: "Cited courts",
  ref: "Statutory references",
  Approved: "Approved for reporting",
};

// Design system v1, per the Document Analysis mockup (docs/architecture/design_reference
// page 12). Two sources, deliberately kept visually separate:
//   left  — written by the language model (summary, points to review)
//   right — extracted by the NER model (parties, dates, references)
// No page references on values: the analysis API doesn't return any.
// With REASONING_V2 on (kb-v2 C4) the response carries "reasoning" (or null
// with "reasoning_error"), and a tab bar offers Summary & entities / Reasoning.
// Without that key the page is exactly as before.
export default function AnalysisResults({ analysis }) {
  const [tab, setTab] = useState("summary");
  if (!("reasoning" in analysis)) return <SummaryAndEntities analysis={analysis} />;
  const tabs = [
    ["summary", "Summary & entities"],
    ["reasoning", `Reasoning${analysis.reasoning ? ` (${analysis.reasoning.counts.kept})` : ""}`],
  ];
  return (
    <div className="mt-12">
      <div className="flex gap-2 border-b border-ds-rule" role="tablist" aria-label="Analysis views">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={`min-h-[48px] px-4 -mb-px font-ds-sans text-[16px] border-b-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink ${
              tab === key ? "border-ds-ink font-semibold text-ds-text" : "border-transparent text-ds-text-2 hover:text-ds-text"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "summary" ? (
        <SummaryAndEntities analysis={analysis} />
      ) : (
        <ReasoningPanel reasoning={analysis.reasoning} error={analysis.reasoning_error} />
      )}
    </div>
  );
}

function SummaryAndEntities({ analysis }) {
  // Risks are shown once, as "Points to review" rows, so drop the summary's
  // own risk section (section 5 of the prompt in AIClient.summarise).
  // With REASONING_V2 (kb-v2 C10) review points the document contradicts are removed, so the list can
  // be empty while the summary's own section still holds them: then the section is dropped too.
  const checked = "review_points_removed" in analysis;
  const summary = analysis.risks.length || checked ? withoutRiskSection(analysis.summary) : analysis.summary;
  const removed = analysis.review_points_removed || 0;
  return (
    <div className="mt-12 grid gap-12 lg:grid-cols-[minmax(0,1fr)_380px] items-start">
      <section>
        <div className="flex flex-wrap items-end justify-between gap-3 pb-4 border-b-2 border-ds-ink">
          <h2 className="ds-h2">AI summary</h2>
          <span className="ds-tag-neutral">AI-generated · read with the original</span>
        </div>
        <Markdown className="mt-6">
          {summary}
        </Markdown>

        <h3 className="ds-h4 mt-10">Points to review</h3>
        {removed > 0 && (
          <p className="ds-meta mt-2">
            {removed} point{removed === 1 ? "" : "s"} removed: {removed === 1 ? "it said" : "they said"} something was
            missing that the document contains.
          </p>
        )}
        {analysis.risks.length === 0 ? (
          <p className="ds-body text-ds-text-2 mt-3">The summary listed no risks or missing clauses.</p>
        ) : (
          <ul className="mt-3 border-t border-ds-rule">
            {analysis.risks.map((r, i) => (
              <li key={i} className="grid grid-cols-[auto_1fr] gap-x-6 py-4 border-b border-ds-rule">
                <span className="ds-tag-review h-7 self-start">
                  <AlertTriangle className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" />
                  Review
                </span>
                <RiskText text={r} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="bg-ds-sheet border border-ds-rule rounded-ds">
        <div className="px-6 pt-6 pb-5 border-b-2 border-ds-ink">
          <h2 className="ds-h3">Extracted data</h2>
          <p className="ds-meta mt-2">
            Found by LegalEase&apos;s entity-recognition model, not the language model. Trained on Pakistani court
            judgments: most reliable on judgments, expect misses on contracts and other documents.
          </p>
        </div>
        <div className="px-6 pb-6">
          {analysis.ner_available ? (
            <NerResults analysis={analysis} />
          ) : (
            <p className="flex items-start gap-2 pt-5 ds-body text-ds-text-2">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              The entity-recognition model isn&apos;t loaded on this server, so parties, dates and references
              weren&apos;t extracted. The AI summary is unaffected.
            </p>
          )}
        </div>
      </aside>
    </div>
  );
}

function NerResults({ analysis }) {
  const groups = Object.entries(analysis.entities || {});
  const total = groups.reduce((n, [, es]) => n + es.length, 0);
  return (
    <>
      <Group title="Parties" items={analysis.parties} empty="No people or organisations found." />
      <Group title="Dates" items={analysis.dates} empty="No dates found." />
      <Group title="References" items={analysis.references} empty="No case numbers, cited cases or statutes found." />

      {groups.length > 0 && (
        <details className="mt-6">
          <summary className="cursor-pointer min-h-[44px] flex items-center font-ds-sans font-semibold text-[15px] text-ds-text rounded-ds
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink">
            All entities by type ({total})
          </summary>
          <table className="w-full text-left mt-2 font-ds-sans text-[14px] leading-[20px]">
            <thead className="border-b-2 border-ds-ink text-ds-text-2">
              <tr>
                <th className="py-2 pr-3 font-semibold">Type</th>
                <th className="py-2 pr-3 font-semibold">Text</th>
                <th className="py-2 pr-3 font-semibold text-right">Mentions</th>
                <th className="py-2 font-semibold text-right">Conf.</th>
              </tr>
            </thead>
            <tbody>
              {groups.flatMap(([type, ents]) =>
                ents.map((e, i) => (
                  <tr key={`${type}-${i}`} className="border-b border-ds-rule align-top">
                    <td className="py-2 pr-3 text-ds-text-2">{i === 0 ? ENTITY_LABELS[type] || type : ""}</td>
                    <td className="py-2 pr-3 text-ds-text">{e.text}</td>
                    <td className="py-2 pr-3 text-right tabular-nums text-ds-text-2">{e.count}</td>
                    <td className="py-2 text-right tabular-nums text-ds-text-2">{e.score.toFixed(2)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </details>
      )}
    </>
  );
}

function Group({ title, items, empty }) {
  return (
    <div className="pt-5">
      <p className="ds-eyebrow">{title}</p>
      {items.length === 0 ? (
        <p className="ds-meta py-3">{empty}</p>
      ) : (
        <ul className="mt-1">
          {items.map((it, i) => (
            <li key={i} className="py-3 border-b border-ds-rule last:border-0 font-ds-sans font-semibold text-[16px] leading-[24px] text-ds-text">
              {it}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Section headings as the summary writes them: "5) Risk flags…",
// "**5. Risk flags**", "### 5) Risk flags" (see backend summary_sections.py).
const RISK_HEADING = /^\s*(?:#{1,6}\s*|\*\*\s*)?5\s*[).:][^\n]*(?:risk|review)[^\n]*$/im;
const LATER_HEADING = /^\s*(?:#{1,6}\s*|\*\*\s*)?[6-9]\s*[).:][^\n]*$/m;

function withoutRiskSection(text) {
  const m = text.match(RISK_HEADING);
  if (!m) return text;
  const before = text.slice(0, m.index);
  const after = text.slice(m.index + m[0].length);
  const next = after.match(LATER_HEADING);
  return (before + (next ? after.slice(next.index) : "")).trim();
}

// "No detailed bail conditions: Standard …" / "Surety details — No requirement …":
// bold the short lead phrase, as the mockup's review rows do. The model uses
// either a colon or a spaced dash, so accept both.
const LEAD = /^(.{3,60}?)(:|\s[—–-]\s)/;

function RiskText({ text }) {
  const m = text.match(LEAD);
  if (!m) return <span className="ds-body">{text}</span>;
  return (
    <span className="ds-body">
      <strong className="font-semibold">{m[1]}</strong>
      {m[2]}
      {text.slice(m[0].length)}
    </span>
  );
}
