import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Briefcase, Loader2, AlertCircle } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { useAuthStore } from "@/store/authStore";
import { ROLES, CASE_TYPES } from "@/constants";
import { casesApi } from "./api";
import { cnInput } from "@/lib/formStyles";

const STATUS_META = {
  created: { dot: "bg-status-pending", label: "Created" },
  assigned: { dot: "bg-status-pending", label: "Assigned" },
  in_progress: { dot: "bg-status-active", label: "In progress" },
  hearing_scheduled: { dot: "bg-status-active", label: "Hearing scheduled" },
  closed: { dot: "bg-ink-muted", label: "Closed" },
};

export default function CasesPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [showCreate, setShowCreate] = useState(false);

  const { data: cases, isLoading, isError, error } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const headerActions = isLawyer && (
    <AppButton onClick={() => setShowCreate((v) => !v)}>
      <Plus className="h-4 w-4" />
      New case
    </AppButton>
  );

  return (
    <AppShell
      title="Cases"
      subtitle={isLawyer ? "Your caseload" : "Cases shared with you by your counsel"}
      headerActions={headerActions}
    >
      <p className="text-sm text-ink-muted mb-6">
        {isLoading
          ? "Loading…"
          : `${cases?.length ?? 0} case${cases?.length === 1 ? "" : "s"}`}
      </p>

      {isLawyer && showCreate && (
        <div className="mb-10">
          <CreateCaseForm onDone={() => setShowCreate(false)} />
        </div>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-ink-muted py-8 justify-center">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading cases…
        </div>
      )}

      {isError && (
        <div className="flex items-start gap-3 py-4 text-sm">
          <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-ink-text">Couldn't load cases.</p>
            <p className="text-ink-muted mt-1">
              {error?.response?.data?.error?.message ||
                "Make sure the backend is running."}
            </p>
          </div>
        </div>
      )}

      {!isLoading && !isError && cases?.length === 0 && (
        <div className="text-center py-12">
          <Briefcase className="h-9 w-9 text-ink-muted/50 mx-auto mb-3" />
          <p className="text-sm font-medium text-ink-text">No cases yet</p>
          <p className="text-sm text-ink-muted mt-1">
            {isLawyer
              ? 'Click "New case" above to file your first matter.'
              : "Your lawyer will share cases with you here."}
          </p>
        </div>
      )}

      {!isLoading && !isError && cases?.length > 0 && (
        <ul>
          {cases.map((c) => (
            <CaseRow key={c.id} case={c} />
          ))}
        </ul>
      )}
    </AppShell>
  );
}

function CaseRow({ case: c }) {
  const meta = STATUS_META[c.status] || {};
  return (
    <li className="border-b border-hairline-subtle last:border-0">
      <Link to={`/cases/${c.id}`} className="flex items-start gap-3 py-4 px-2 -mx-2 group hover:bg-hairline-subtle/40 transition-colors">
        <span className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${meta.dot || "bg-ink-muted"}`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h3 className="text-sm font-medium text-ink-text truncate">
              {c.title}
            </h3>
            <span className="text-xs text-ink-muted shrink-0">{meta.label || c.status}</span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-ink-muted">
            <span>{c.case_type}</span>
            {c.court_code && <span>· {c.court_code}</span>}
            {c.filing_date && <span>· filed {c.filing_date}</span>}
          </div>
          {c.description && (
            <p className="mt-1.5 text-sm text-ink-muted line-clamp-2">{c.description}</p>
          )}
        </div>
      </Link>
    </li>
  );
}

function CreateCaseForm({ onDone }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState(CASE_TYPES.DIVORCE);
  const [courtCode, setCourtCode] = useState("");
  const [clientEmail, setClientEmail] = useState("");

  const { mutate, isPending } = useMutation({
    mutationFn: (payload) => casesApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["case-stats"] });
      toast.success("Case created.");
      onDone();
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not create case.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const submit = (e) => {
    e.preventDefault();
    mutate({
      title,
      description: description || null,
      case_type: caseType,
      court_code: courtCode || null,
      client_email: clientEmail.trim() || null,
    });
  };

  return (
    <PanelCard
      title="New case"
      description="Fill the case details and optionally link a registered client by email — they'll see this case in their dashboard immediately."
    >
      <form onSubmit={submit} className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="block text-sm text-ink-muted mb-1.5">Title</label>
          <input
            placeholder="e.g. Khan v. Khan — Custody"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            minLength={3}
            className={cnInput(false)}
          />
        </div>
        <div>
          <label className="block text-sm text-ink-muted mb-1.5">Case type</label>
          <select
            value={caseType}
            onChange={(e) => setCaseType(e.target.value)}
            className={cnInput(false)}
          >
            {Object.values(CASE_TYPES).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-ink-muted mb-1.5">Court (optional)</label>
          <input
            placeholder="Family Court Islamabad"
            value={courtCode}
            onChange={(e) => setCourtCode(e.target.value)}
            className={cnInput(false)}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="block text-sm text-ink-muted mb-1.5">Client email (optional)</label>
          <input
            type="email"
            placeholder="client@example.com"
            value={clientEmail}
            onChange={(e) => setClientEmail(e.target.value)}
            className={cnInput(false)}
          />
          <p className="text-xs text-ink-muted mt-1.5">
            If the client is already registered, this case will appear on their
            dashboard. Leave blank to assign later.
          </p>
        </div>
        <div className="sm:col-span-2">
          <label className="block text-sm text-ink-muted mb-1.5">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className={cnInput(false)}
            placeholder="Brief summary of the matter..."
          />
        </div>
        <div className="sm:col-span-2 flex items-center gap-4 mt-2">
          <AppButton type="submit" disabled={isPending || title.length < 3}>
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create case"}
          </AppButton>
          <AppButton type="button" variant="secondary" onClick={onDone}>
            Cancel
          </AppButton>
        </div>
      </form>
    </PanelCard>
  );
}
