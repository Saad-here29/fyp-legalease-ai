import { Link } from "react-router-dom";
import { AlertCircle, AlertTriangle, Check } from "lucide-react";
import { judgmentPath, kbRecordPath } from "@/features/knowledge-base/kbFormat";

// Document Analysis "Reasoning" tab (kb-v2 C4, REASONING_V2). Every item was
// quoted from the document by the model and the quote was found in the text
// by LegalEase before it was kept (backend app/ai/reasoning.py); items that
// failed are removed and counted. Statutes link to the Knowledge Base record
// when the Act and section were found there; related cases are past
// judgments from the library, never claims about this document.

const PARTY = (p) => p.charAt(0).toUpperCase() + p.slice(1);

export default function ReasoningPanel({ reasoning, error }) {
  if (!reasoning) {
    return (
      <p className="mt-8 flex items-start gap-2 ds-body text-ds-text-2 max-w-[760px]" role="note">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
        {error || "The reasoning step didn't run for this analysis."}
      </p>
    );
  }
  const c = reasoning.counts;
  const parties = Object.entries(reasoning.arguments || {});
  return (
    <div className="mt-8 max-w-[860px]">
      <div className="flex flex-wrap items-center gap-3">
        <span className="ds-tag-neutral">{reasoning.disclaimer}</span>
        {c.dropped > 0 && (
          <span className="ds-tag-review">
            <AlertTriangle className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" />
            {c.dropped} unverifiable item{c.dropped === 1 ? "" : "s"} removed
          </span>
        )}
        <span className="ds-meta">
          {c.kept} kept of {c.returned}
          {c.flagged ? ` · ${c.flagged} flagged` : ""}
        </span>
      </div>
      {c.dropped > 0 && (
        <p className="ds-meta mt-2">
          Removed because{" "}
          {Object.entries(c.dropped_reasons)
            .map(([r, n]) => `${r} (${n})`)
            .join("; ")}
          .
        </p>
      )}
      {reasoning.coverage?.partial && (
        <p className="mt-4 bg-ds-review-tint text-ds-review px-4 py-3 rounded-ds font-ds-sans font-semibold text-[15px]" role="note">
          {reasoning.coverage.note}
        </p>
      )}
      {reasoning.document_type && (
        <p className="ds-body mt-6">
          <span className="ds-eyebrow mr-2">Document</span>
          {reasoning.document_type.text}
        </p>
      )}

      <Section title="Issues" items={reasoning.issues} empty="No issue could be quoted from the document."
        extra={(i) => <Related cases={i.related_cases} />} />
      {reasoning.related_cases_note && reasoning.issues.some((i) => i.related_cases?.length) && (
        <p className="ds-meta mt-2">{reasoning.related_cases_note}</p>
      )}

      <h3 className="ds-h4 mt-10">Arguments by party</h3>
      {parties.length === 0 ? (
        <p className="ds-meta mt-3">No arguments could be quoted from the document.</p>
      ) : (
        parties.map(([party, items]) => <Section key={party} title={PARTY(party)} items={items} small />)
      )}

      <Section title="Court's reasoning" items={reasoning.court_reasoning} numbered
        empty="No reasoning steps could be quoted from the document." />

      <h3 className="ds-h4 mt-10">Holding</h3>
      {reasoning.holding_or_outcome ? (
        <ul className="mt-3 border-t border-ds-rule"><Item item={reasoning.holding_or_outcome} /></ul>
      ) : (
        <p className="ds-meta mt-3">No holding or outcome could be quoted from the document.</p>
      )}

      <Statutes items={reasoning.statutes_cited} />
      <Section title="Strong points" items={reasoning.strong_points} empty="None quoted." />
      <Section title="Weak points" items={reasoning.weak_points} empty="None quoted." />
      <Section title="Risks" items={reasoning.risks} empty="None quoted." />
      <Section title="Open questions" items={reasoning.open_questions} empty="None quoted." />
    </div>
  );
}

function Section({ title, items, empty, numbered = false, small = false, extra }) {
  return (
    <>
      <h3 className={small ? "ds-eyebrow mt-6" : "ds-h4 mt-10"}>{title}</h3>
      {!items?.length ? (
        <p className="ds-meta mt-3">{empty}</p>
      ) : (
        <ul className="mt-3 border-t border-ds-rule">
          {items.map((it, i) => (
            <Item key={i} item={it} number={numbered ? it.step || i + 1 : null}>
              {extra?.(it)}
            </Item>
          ))}
        </ul>
      )}
    </>
  );
}

function Item({ item, number, children }) {
  return (
    <li className="py-4 border-b border-ds-rule">
      <div className="grid grid-cols-[auto_1fr_auto] gap-x-4 items-start">
        <span className="ds-meta tabular-nums w-6">{number != null ? `${number}.` : ""}</span>
        <span className="ds-body">{item.text}</span>
        <Verified item={item} />
      </div>
      <details className="mt-2 ml-10">
        <summary className="cursor-pointer ds-meta min-h-[32px] inline-flex items-center rounded-ds focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink">
          Evidence
        </summary>
        <blockquote className="mt-2 border-l-4 border-ds-rule pl-4 ds-body text-ds-text-2 italic" dir="auto">
          “{item.evidence}”
        </blockquote>
      </details>
      {item.flags?.length > 0 && <p className="ds-meta text-ds-review mt-2 ml-10">{item.flags.join("; ")}</p>}
      {children}
    </li>
  );
}

function Verified({ item }) {
  return item.verified ? (
    <span className="inline-flex items-center gap-1 font-ds-sans font-semibold text-[13px] text-ds-pass whitespace-nowrap"
      title="The quote was found in the document">
      <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" /> Quote found
    </span>
  ) : (
    <span className="ds-tag-review whitespace-nowrap" title="The quote was found, but something it names wasn't">
      Check
    </span>
  );
}

const STATUS = {
  verified: ["Verified in the Knowledge Base", "text-ds-pass"],
  not_found: ["Section not in our copy", "text-ds-review"],
  not_checked: ["Not checked (Act not held)", "text-ds-text-2"],
};

function Statutes({ items }) {
  return (
    <>
      <h3 className="ds-h4 mt-10">Statutes cited</h3>
      {!items?.length ? (
        <p className="ds-meta mt-3">No statute could be quoted from the document.</p>
      ) : (
        <ul className="mt-3 border-t border-ds-rule">
          {items.map((s, i) => {
            const [label, cls] = STATUS[s.status] || STATUS.not_checked;
            const to = s.kb_record_id ? kbRecordPath(s.kb_record_id) : null;
            return (
              <Item key={i} item={{ ...s, text: `${s.act} s.${s.section}${s.heading ? ` (${s.heading})` : ""}` }}>
                <p className={`ml-10 mt-2 font-ds-sans text-[14px] font-semibold ${cls}`}>
                  {label}
                  {to && (
                    <>
                      {" · "}
                      <Link to={to} className="ds-link">Open {s.kb_title} s.{s.section}</Link>
                    </>
                  )}
                  {s.note && s.status !== "verified" && <span className="font-normal text-ds-text-2"> · {s.note}</span>}
                </p>
              </Item>
            );
          })}
        </ul>
      )}
    </>
  );
}

function Related({ cases }) {
  if (!cases?.length) return null;
  return (
    <div className="ml-10 mt-3">
      <p className="ds-meta">Related past cases (not cited in this document)</p>
      <ul className="mt-1">
        {cases.map((c) => (
          <li key={c.doc_id}>
            <Link to={judgmentPath(c.doc_id, c.paragraph)} className="ds-link text-[15px]">
              {c.display_name}
              {c.court || c.year ? ` (${[c.court, c.year].filter(Boolean).join(", ")})` : ""}, para {c.paragraph}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
