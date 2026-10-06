import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertCircle, Check, X } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import Markdown from "@/lib/Markdown";
import { contractsApi } from "./api";
import { CONTRACT_TEMPLATES } from "./templates";

// One drafted contract — design system v1, per the Contracts mockup
// (docs/design_reference page 13): the contract as a document on Sheet, the
// compliance check beside it, then version history. Adapted: no "Export
// .docx" and no "Fix failing item" (neither exists); the compliance check is
// the backend's deterministic keyword check — pass or fail per required
// clause, no "review" state.

const fmtDateTime = (v) =>
  new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function ContractDetailPage() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const qc = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [fresh, setFresh] = useState(null);
  const [draftText, setDraftText] = useState(null); // non-null while editing

  const contractQuery = useQuery({ queryKey: ["contract", id], queryFn: () => contractsApi.get(id) });
  const versionsQuery = useQuery({
    queryKey: ["contract-versions", id],
    queryFn: () => contractsApi.versions(id),
    enabled: !!contractQuery.data,
  });

  const check = useMutation({
    mutationFn: (v) => contractsApi.checkCompliance(id, v),
    onSuccess: (result) => {
      setFresh(result);
      qc.invalidateQueries({ queryKey: ["contract-versions", id] });
      const missing = result.results.some((r) => !r.passed);
      const blanks = result.unfilled_placeholders?.length > 0;
      if (result.all_passed) toast.success("All required clauses found, no unfilled placeholders.");
      else if (missing && blanks) toast.warning("Some required clauses are missing, and placeholders are unfilled.");
      else if (missing) toast.warning("Some required clauses are missing.");
      else toast.warning("All clauses found, but the draft has unfilled placeholders.");
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not run the compliance check.", {
        description: e?.response?.data?.error?.hint,
      }),
  });

  const save = useMutation({
    mutationFn: (content) => contractsApi.edit(id, content),
    onSuccess: (v) => {
      setDraftText(null);
      setSelected(v.version_number);
      setFresh(null);
      qc.invalidateQueries({ queryKey: ["contract", id] });
      qc.invalidateQueries({ queryKey: ["contract-versions", id] });
      const r = v.compliance_result;
      if (r?.all_passed) toast.success(`Saved as version ${v.version_number}. All required clauses found.`);
      else toast.warning(`Saved as version ${v.version_number}. The compliance check found problems; see the panel.`);
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not save the edit.", {
        description: e?.response?.data?.error?.hint,
      }),
  });

  const back = <Link to={ROUTES.CONTRACTS} className="ds-link font-medium">Contracts</Link>;

  if (contractQuery.isLoading || contractQuery.isError) {
    return (
      <AppShell eyebrow={back} title="Contract">
        {contractQuery.isLoading ? (
          <p className="flex items-center gap-3 ds-body text-ds-text-2">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading contract…
          </p>
        ) : (
          <p className="flex items-start gap-2 ds-body text-ds-seal" role="alert">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            {contractQuery.error?.response?.data?.error?.message || "Could not load this contract."}
          </p>
        )}
      </AppShell>
    );
  }

  const contract = contractQuery.data;
  const versions = versionsQuery.data?.length ? versionsQuery.data : [contract.latest_version];
  const label = CONTRACT_TEMPLATES[contract.contract_type]?.label || contract.contract_type;
  const active = versions.find((v) => v.version_number === selected) || contract.latest_version;
  // A fresh check (local state) wins over the result stored on the version.
  const compliance = fresh && fresh.version_number === active.version_number ? fresh : active.compliance_result;

  return (
    <AppShell
      eyebrow={back}
      title={contract.title || label}
      subtitle={`${label} · version ${active.version_number} · ${fmtDateTime(active.created_at)}`}
      headerActions={
        isLawyer && (
          <>
          {draftText === null ? (
            <button className="ds-btn-secondary" onClick={() => setDraftText(active.content)}>
              Edit draft
            </button>
          ) : (
            <>
              <button className="ds-btn-secondary" onClick={() => setDraftText(null)} disabled={save.isPending}>
                Cancel
              </button>
              <button className="ds-btn-primary" onClick={() => save.mutate(draftText)}
                disabled={save.isPending || draftText.trim() === active.content.trim()}>
                {save.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Saving" /> : "Save as new version"}
              </button>
            </>
          )}
          {draftText === null && (
          <button
            className={compliance ? "ds-btn-secondary" : "ds-btn-primary"}
            disabled={check.isPending}
            onClick={() => check.mutate(active.version_number)}
          >
            {check.isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Checking…
              </>
            ) : compliance ? (
              "Re-run compliance check"
            ) : (
              "Check compliance"
            )}
          </button>
          )}
          </>
        )
      }
    >
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_340px] items-start">
        {draftText !== null ? (
          <div className="min-w-0">
            <label htmlFor="contract-edit" className="ds-label">
              Editing version {active.version_number}. Saving creates version {versions[versions.length - 1].version_number + 1} and re-runs the checks.
            </label>
            <textarea
              id="contract-edit"
              value={draftText}
              onChange={(e) => setDraftText(e.target.value)}
              rows={28}
              className="ds-input py-3 font-mono text-[14px] leading-[22px]"
            />
          </div>
        ) : (
        <article className="bg-ds-sheet border border-ds-rule rounded-ds px-6 sm:px-12 py-10 min-w-0">
          <Markdown
           
            className="font-ds-serif text-[18px] leading-[30px] prose-headings:font-ds-serif prose-headings:font-medium
              prose-h1:text-center prose-h1:uppercase prose-h1:tracking-[0.12em] prose-h1:text-[22px]"
          >
            {active.content}
          </Markdown>
        </article>
        )}

        <aside className="space-y-10">
          <Compliance result={compliance} isLawyer={isLawyer} />

          <section>
            <h2 className="ds-h4 pb-3 border-b-2 border-ds-ink">Version history</h2>
            <ul>
              {versions
                .slice()
                .reverse()
                .map((v) => {
                  const on = v.version_number === active.version_number;
                  return (
                    <li key={v.id} className="border-b border-ds-rule">
                      <button
                        onClick={() => setSelected(v.version_number)}
                        aria-current={on ? "true" : undefined}
                        className={`relative w-full text-left py-3 pl-4 pr-2 min-h-[56px] ${on ? "bg-ds-sheet" : "hover:bg-ds-sheet/60"}
                          focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink`}
                      >
                        {on && <span className="absolute left-0 inset-y-0 w-1 bg-ds-seal" aria-hidden="true" />}
                        <span className={`block font-ds-sans text-[16px] ${on ? "font-semibold" : ""}`}>Version {v.version_number}</span>
                        <span className="ds-meta">{fmtDateTime(v.created_at)}</span>
                      </button>
                    </li>
                  );
                })}
            </ul>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}

// Snippets are cut from the markdown contract text; drop the markup.
const plain = (s) => s.replace(/\*\*|__|`|^#+\s*/gm, "").replace(/\s+/g, " ").trim();

function Compliance({ result, isLawyer }) {
  if (!result) {
    return (
      <section>
        <h2 className="ds-h3">Compliance check</h2>
        <p className="ds-body text-ds-text-2 mt-2">
          {isLawyer
            ? "Not run on this version yet. The check looks for each clause this template requires — a keyword check, not another AI call."
            : "Your lawyer hasn't run the compliance check on this version."}
        </p>
      </section>
    );
  }
  // Unfilled placeholders are one more row; results saved before that check
  // existed (unfilled_placeholders missing) simply don't show it.
  const blanks = result.unfilled_placeholders;
  const rows = [
    ...result.results.map((r) => ({
      name: r.name,
      passed: r.passed,
      detail: r.passed ? (r.matched_snippet ? `“…${plain(r.matched_snippet)}…”` : "Found") : "Not found in this version",
    })),
    ...(blanks
      ? [{
          name: blanks.length ? "Unfilled placeholders" : "No unfilled placeholders",
          passed: blanks.length === 0,
          detail: blanks.length ? `Fill in before use: ${blanks.join(", ")}` : "No [address]-style blanks left",
        }]
      : []),
  ];
  const passed = rows.filter((r) => r.passed).length;
  const failed = rows.length - passed;
  return (
    <section>
      <h2 className="ds-h3">Compliance check</h2>
      <p className="font-ds-sans font-semibold text-[17px] mt-2">
        <span className="text-ds-pass">{passed} pass</span>
        {failed > 0 && <span className="text-ds-seal"> · {failed} fail{failed === 1 ? "s" : ""}</span>}
      </p>
      <div className="flex h-1.5 gap-0.5 mt-3" aria-hidden="true">
        {rows.map((r) => (
          <span key={r.name} className={`flex-1 rounded-ds-sm ${r.passed ? "bg-ds-pass" : "bg-ds-seal"}`} />
        ))}
      </div>
      <ul className="mt-4 border-t-2 border-ds-ink">
        {rows.map((r) => (
          <li key={r.name} className="grid grid-cols-[32px_1fr] gap-x-3 py-4 border-b border-ds-rule">
            <span
              className={`h-7 w-7 rounded-ds flex items-center justify-center ${
                r.passed ? "bg-ds-pass-tint text-ds-pass" : "bg-ds-seal-tint text-ds-seal"
              }`}
            >
              {r.passed ? <Check className="h-4 w-4" strokeWidth={2.5} /> : <X className="h-4 w-4" strokeWidth={2.5} />}
              <span className="sr-only">{r.passed ? "Passes" : "Fails"}</span>
            </span>
            <span className="min-w-0">
              <span className="block font-ds-sans font-semibold text-[16px] leading-[24px]">{r.name}</span>
              <span className="ds-meta block mt-0.5 break-words">{r.detail}</span>
            </span>
          </li>
        ))}
      </ul>
      {result.checked_at && <p className="ds-meta mt-3">Checked {fmtDateTime(result.checked_at)}</p>}
    </section>
  );
}
