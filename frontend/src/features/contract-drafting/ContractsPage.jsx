import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, CONTRACT_TYPES } from "@/constants";
import { fmtDate } from "@/features/case-management/caseMeta";
import { contractsApi } from "./api";
import { CONTRACT_TEMPLATES } from "./templates";

// Contracts — design system v1, per the Contracts mockup (docs/architecture/design_reference
// page 13): template cards, then the drafted contracts. Only the three real
// templates (NDA, Employment, Service Agreement), not the mockup's five.

export default function ContractsPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [showDraft, setShowDraft] = useState(false);

  const { data: contracts, isLoading, isError, error } = useQuery({
    queryKey: ["contracts"],
    queryFn: contractsApi.list,
  });
  const n = contracts?.length ?? 0;

  return (
    <AppShell
      title="Contracts"
      subtitle={
        isLoading
          ? isLawyer ? "Drafted for your clients" : "Contracts shared with you"
          : `${n} contract${n === 1 ? "" : "s"} · ${isLawyer ? "drafted for your clients" : "shared with you"}`
      }
      headerActions={
        isLawyer && (
          <button onClick={() => setShowDraft((v) => !v)} className={showDraft ? "ds-btn-secondary" : "ds-btn-primary"}>
            {showDraft ? "Close" : "New contract"}
          </button>
        )
      }
    >
      {isLawyer && showDraft && <DraftContractForm onDone={() => setShowDraft(false)} />}

      {isLoading && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading contracts…
        </p>
      )}

      {isError && (
        <p className="flex items-start gap-2 ds-body text-ds-seal" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          {error?.response?.data?.error?.message || "Couldn't load contracts. Make sure the backend is running."}
        </p>
      )}

      {!isLoading && !isError && n === 0 && (
        <section className="ds-section">
          <p className="ds-h4">No contracts yet</p>
          <p className="ds-body text-ds-text-2 mt-1">
            {isLawyer ? "Use “New contract” to draft your first one." : "Your lawyer will share drafted contracts with you here."}
          </p>
        </section>
      )}

      {!isLoading && !isError && n > 0 && (
        <table className="w-full font-ds-sans text-left">
          <thead className="border-b-2 border-ds-ink">
            <tr className="text-[15px] text-ds-text-2">
              <th className="font-semibold pb-3 pr-6">Contract</th>
              <th className="font-semibold pb-3 pr-6 hidden sm:table-cell">Template</th>
              <th className="font-semibold pb-3">Updated</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map((c) => {
              const label = CONTRACT_TEMPLATES[c.contract_type]?.label || c.contract_type;
              return (
                <tr key={c.id} className="border-b border-ds-rule hover:bg-ds-sheet/60">
                  <td className="py-4 pr-6">
                    <Link
                      to={`/contracts/${c.id}`}
                      className="font-semibold text-[17px] leading-[24px] text-ds-text hover:underline decoration-ds-underline decoration-2 underline-offset-4
                        focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink rounded-ds-sm"
                    >
                      {c.title || label}
                    </Link>
                  </td>
                  <td className="py-4 pr-6 ds-body hidden sm:table-cell">{label}</td>
                  <td className="py-4 ds-body text-ds-text-2 whitespace-nowrap">{fmtDate(c.updated_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </AppShell>
  );
}

function DraftContractForm({ onDone }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [contractType, setContractType] = useState(CONTRACT_TYPES.NDA);
  const [title, setTitle] = useState("");
  const [fields, setFields] = useState({});
  const template = CONTRACT_TEMPLATES[contractType];

  const { mutate, isPending } = useMutation({
    mutationFn: (payload) => contractsApi.draft(payload),
    onSuccess: (contract) => {
      qc.invalidateQueries({ queryKey: ["contracts"] });
      toast.success("Contract drafted.");
      onDone();
      navigate(`/contracts/${contract.id}`);
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not draft contract.", {
        description: e?.response?.data?.error?.hint,
      }),
  });

  const allFilled = template.fields.every((f) => (fields[f.key] || "").trim());

  return (
    <section className="ds-section mb-12">
      <h2 className="ds-h3">Draft a new contract</h2>
      <p className="ds-body text-ds-text-2 mt-1 max-w-[680px]">
        Pick a template and fill in the details; the AI writes the full contract text. This takes several seconds.
      </p>

      <form
        className="mt-6"
        onSubmit={(e) => {
          e.preventDefault();
          mutate({ contract_type: contractType, fields, title: title || null });
        }}
      >
        <p className="ds-eyebrow mb-3" id="template-label">Template</p>
        <div role="radiogroup" aria-labelledby="template-label" className="grid gap-3 sm:grid-cols-3">
          {Object.entries(CONTRACT_TEMPLATES).map(([type, t]) => {
            const active = type === contractType;
            return (
              <button
                type="button"
                role="radio"
                aria-checked={active}
                key={type}
                onClick={() => {
                  setContractType(type);
                  setFields({});
                }}
                className={`text-left px-5 py-4 min-h-[72px] rounded-ds border-2 transition-colors
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ds-ink ${
                  active ? "border-ds-seal bg-ds-seal-tint" : "border-ds-rule bg-ds-sheet hover:border-ds-text-2"
                }`}
              >
                <span className="block font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text">{t.label}</span>
                <span className="block ds-meta mt-0.5">{t.summary}</span>
              </button>
            );
          })}
        </div>

        <div className="grid gap-6 sm:grid-cols-2 mt-8 max-w-[760px]">
          <div className="sm:col-span-2">
            <label htmlFor="ct-title" className="ds-label">
              Title <span className="font-normal text-ds-text-2">(optional)</span>
            </label>
            <input id="ct-title" placeholder={template.label} value={title} onChange={(e) => setTitle(e.target.value)} className="ds-input" />
          </div>
          {template.fields.map((f) => (
            <div key={f.key}>
              <label htmlFor={`ct-${f.key}`} className="ds-label">{f.label}</label>
              <input
                id={`ct-${f.key}`}
                value={fields[f.key] || ""}
                onChange={(e) => setFields((prev) => ({ ...prev, [f.key]: e.target.value }))}
                required
                className="ds-input"
              />
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 mt-8">
          <button type="submit" disabled={isPending || !allFilled} className="ds-btn-primary">
            {isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Drafting…
              </>
            ) : (
              "Draft contract"
            )}
          </button>
          <button type="button" onClick={onDone} disabled={isPending} className="ds-btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}
