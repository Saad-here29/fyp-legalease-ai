import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, FileSignature, Loader2, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES, CONTRACT_TYPES } from "@/constants";
import { cnInput } from "@/lib/formStyles";
import { contractsApi } from "./api";
import { CONTRACT_TEMPLATES } from "./templates";

export default function ContractsPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [showDraft, setShowDraft] = useState(false);

  const { data: contracts, isLoading, isError, error } = useQuery({
    queryKey: ["contracts"],
    queryFn: contractsApi.list,
  });

  const headerActions = isLawyer && (
    <AppButton onClick={() => setShowDraft((v) => !v)}>
      <Plus className="h-4 w-4" />
      New contract
    </AppButton>
  );

  return (
    <AppShell
      title="Contracts"
      subtitle={isLawyer ? "Drafted for your clients" : "Contracts shared with you"}
      headerActions={headerActions}
    >
      <p className="text-sm text-ink-muted mb-6">
        {isLoading
          ? "Loading…"
          : `${contracts?.length ?? 0} contract${contracts?.length === 1 ? "" : "s"}`}
      </p>

      {isLawyer && showDraft && (
        <div className="mb-10">
          <DraftContractForm onDone={() => setShowDraft(false)} />
        </div>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-ink-muted py-8 justify-center">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading contracts…
        </div>
      )}

      {isError && (
        <div className="flex items-start gap-3 py-4 text-sm">
          <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-ink-text">Couldn't load contracts.</p>
            <p className="text-ink-muted mt-1">
              {error?.response?.data?.error?.message ||
                "Make sure the backend is running."}
            </p>
          </div>
        </div>
      )}

      {!isLoading && !isError && contracts?.length === 0 && (
        <div className="text-center py-12">
          <FileSignature className="h-9 w-9 text-ink-muted/50 mx-auto mb-3" />
          <p className="text-sm font-medium text-ink-text">No contracts yet</p>
          <p className="text-sm text-ink-muted mt-1">
            {isLawyer
              ? 'Click "New contract" above to draft your first one.'
              : "Your lawyer will share drafted contracts with you here."}
          </p>
        </div>
      )}

      {!isLoading && !isError && contracts?.length > 0 && (
        <ul>
          {contracts.map((c) => (
            <ContractRow key={c.id} contract={c} />
          ))}
        </ul>
      )}
    </AppShell>
  );
}

function ContractRow({ contract: c }) {
  const label = CONTRACT_TEMPLATES[c.contract_type]?.label || c.contract_type;
  return (
    <li className="border-b border-hairline-subtle last:border-0">
      <Link
        to={`/contracts/${c.id}`}
        className="flex items-start gap-3 py-4 px-2 -mx-2 hover:bg-hairline-subtle/40 transition-colors"
      >
        <FileSignature className="h-4 w-4 text-ink-muted mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h3 className="text-sm font-medium text-ink-text truncate">
              {c.title || label}
            </h3>
            <span className="text-xs text-ink-muted shrink-0">{label}</span>
          </div>
          <div className="mt-1 text-xs text-ink-muted">
            Updated {new Date(c.updated_at).toLocaleDateString()}
          </div>
        </div>
      </Link>
    </li>
  );
}

function DraftContractForm({ onDone }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [contractType, setContractType] = useState(CONTRACT_TYPES.NDA);
  const [title, setTitle] = useState("");
  const [fields, setFields] = useState({});

  const template = CONTRACT_TEMPLATES[contractType];

  const selectType = (type) => {
    setContractType(type);
    setFields({});
  };

  const setField = (key, value) => setFields((f) => ({ ...f, [key]: value }));

  const { mutate, isPending } = useMutation({
    mutationFn: (payload) => contractsApi.draft(payload),
    onSuccess: (contract) => {
      qc.invalidateQueries({ queryKey: ["contracts"] });
      toast.success("Contract drafted.");
      onDone();
      navigate(`/contracts/${contract.id}`);
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not draft contract.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const submit = (e) => {
    e.preventDefault();
    mutate({
      contract_type: contractType,
      fields,
      title: title || null,
    });
  };

  const allFieldsFilled = template.fields.every((f) => (fields[f.key] || "").trim());

  return (
    <PanelCard
      title="Draft a new contract"
      description="Pick a template, fill in the details, and the AI will generate the full contract text. This can take several seconds."
    >
      <form onSubmit={submit} className="space-y-5">
        <div>
          <span className="block text-sm text-ink-muted mb-2">Template</span>
          <div className="flex border border-hairline rounded-md overflow-hidden">
            {Object.entries(CONTRACT_TEMPLATES).map(([type, t], i) => (
              <button
                type="button"
                key={type}
                onClick={() => selectType(type)}
                className={`flex-1 text-sm py-2 px-2 transition-colors ${
                  i > 0 ? "border-l border-hairline" : ""
                } ${
                  contractType === type
                    ? "bg-ink-panel text-paper"
                    : "text-ink-muted hover:text-ink-text hover:bg-hairline-subtle/50"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-ink-muted mb-1.5">Title (optional)</label>
          <input
            placeholder={template.label}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={cnInput(false)}
          />
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {template.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-sm text-ink-muted mb-1.5">{f.label}</label>
              <input
                value={fields[f.key] || ""}
                onChange={(e) => setField(f.key, e.target.value)}
                required
                className={cnInput(false)}
              />
            </div>
          ))}
        </div>

        <div className="flex items-center gap-4 mt-2">
          <AppButton type="submit" disabled={isPending || !allFieldsFilled}>
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Drafting…
              </>
            ) : (
              "Draft contract"
            )}
          </AppButton>
          <AppButton type="button" variant="secondary" onClick={onDone} disabled={isPending}>
            Cancel
          </AppButton>
        </div>
      </form>
    </PanelCard>
  );
}
