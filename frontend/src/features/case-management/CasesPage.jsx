import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertCircle, Search } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, CASE_TYPES } from "@/constants";
import { casesApi } from "./api";
import StatusTag from "./StatusTag";
import { TYPE_LABEL, fmtDate } from "./caseMeta";

// Cases list — design system v1, per the Cases mockup (docs/design_reference
// page 8): status tabs, search, a ruled table and paging. Adapted to the
// data that exists: no next-hearing or client columns (cases carry no
// hearing dates, and the list has no client names) — "Updated" instead.

const PAGE_SIZE = 10;

const TABS = [
  { key: "open", label: "Open", test: (c) => c.status !== "closed" },
  { key: "hearing", label: "Hearing scheduled", test: (c) => c.status === "hearing_scheduled" },
  { key: "closed", label: "Closed", test: (c) => c.status === "closed" },
  { key: "all", label: "All", test: () => true },
];

export default function CasesPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState("open");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  const { data: cases, isLoading, isError, error } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const all = useMemo(() => cases || [], [cases]);
  const counts = Object.fromEntries(TABS.map((t) => [t.key, all.filter(t.test).length]));
  const q = query.trim().toLowerCase();
  const rows = all
    .filter(TABS.find((t) => t.key === tab).test)
    .filter((c) => !q || [c.title, c.court_code, c.case_type, c.description].some((v) => v?.toLowerCase().includes(q)));
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const current = Math.min(page, pages - 1);
  const shown = rows.slice(current * PAGE_SIZE, (current + 1) * PAGE_SIZE);

  const selectTab = (key) => {
    setTab(key);
    setPage(0);
  };

  return (
    <AppShell
      title="Cases"
      subtitle={
        isLoading
          ? isLawyer ? "Your caseload" : "Cases shared with you by your counsel"
          : `${counts.open} open · ${counts.all} in total`
      }
      headerActions={
        isLawyer && (
          <button onClick={() => setShowCreate((v) => !v)} className={showCreate ? "ds-btn-secondary" : "ds-btn-primary"}>
            {showCreate ? "Close form" : "New case"}
          </button>
        )
      }
    >
      {isLawyer && showCreate && <CreateCaseForm onDone={() => setShowCreate(false)} />}

      <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4 border-b border-ds-rule">
        <div role="tablist" aria-label="Filter cases by status" className="flex flex-wrap gap-x-7 -mb-px">
          {TABS.map((t) => {
            const active = t.key === tab;
            return (
              <button
                key={t.key}
                role="tab"
                aria-selected={active}
                onClick={() => selectTab(t.key)}
                className={`min-h-[48px] font-ds-sans text-[16px] border-b-2 transition-colors
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink ${
                  active ? "border-ds-seal font-semibold text-ds-text" : "border-transparent text-ds-text-2 hover:text-ds-text"
                }`}
              >
                {t.label} <span className="tabular-nums">{isLoading ? "" : counts[t.key]}</span>
              </button>
            );
          })}
        </div>
        <label className="relative w-full sm:w-[320px] mb-3">
          <span className="sr-only">Search cases</span>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-ds-text-2" aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="Title, court or type"
            className="ds-input pl-12"
          />
        </label>
      </div>

      {isLoading && (
        <p className="flex items-center gap-3 py-10 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Loading cases…
        </p>
      )}

      {isError && (
        <p className="flex items-start gap-2 py-8 ds-body text-ds-seal" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          {error?.response?.data?.error?.message || "Couldn't load cases. Make sure the backend is running."}
        </p>
      )}

      {!isLoading && !isError && shown.length === 0 && (
        <div className="py-12">
          <p className="ds-h4">{all.length === 0 ? "No cases yet" : "No cases match"}</p>
          <p className="ds-body text-ds-text-2 mt-1">
            {all.length === 0
              ? isLawyer
                ? "Use “New case” to open your first matter."
                : "Your lawyer will share cases with you here."
              : "Try another tab or search."}
          </p>
        </div>
      )}

      {!isLoading && !isError && shown.length > 0 && (
        <>
          <table className="w-full mt-6 font-ds-sans text-left">
            <thead className="border-b-2 border-ds-ink">
              <tr className="text-[15px] text-ds-text-2">
                <th className="font-semibold pb-3 pr-6">Case</th>
                <th className="font-semibold pb-3 pr-6 hidden md:table-cell">Court</th>
                <th className="font-semibold pb-3 pr-6 hidden sm:table-cell">Updated</th>
                <th className="font-semibold pb-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((c) => (
                <tr key={c.id} className="border-b border-ds-rule align-middle hover:bg-ds-sheet/60">
                  <td className="py-4 pr-6">
                    <Link
                      to={`/cases/${c.id}`}
                      className="block font-semibold text-[17px] leading-[24px] text-ds-text hover:underline decoration-ds-underline decoration-2 underline-offset-4
                        focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink rounded-ds-sm"
                    >
                      {c.title}
                    </Link>
                    <span className="ds-meta">
                      {TYPE_LABEL[c.case_type] || c.case_type}
                      {c.filing_date && ` · filed ${fmtDate(c.filing_date)}`}
                    </span>
                  </td>
                  <td className="py-4 pr-6 ds-body hidden md:table-cell">{c.court_code || <span className="text-ds-text-2">—</span>}</td>
                  <td className="py-4 pr-6 ds-body text-ds-text-2 whitespace-nowrap hidden sm:table-cell">{fmtDate(c.updated_at)}</td>
                  <td className="py-4">
                    <StatusTag status={c.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex flex-wrap items-center justify-between gap-4 mt-6">
            <p className="ds-body text-ds-text-2">
              Showing {current * PAGE_SIZE + 1}–{current * PAGE_SIZE + shown.length} of {rows.length}
            </p>
            {pages > 1 && (
              <div className="flex gap-3">
                <button className="ds-btn-secondary" disabled={current === 0} onClick={() => setPage(current - 1)}>
                  Previous
                </button>
                <button className="ds-btn-secondary" disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>
                  Next
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </AppShell>
  );
}

function CreateCaseForm({ onDone }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState(CASE_TYPES.DIVORCE);
  const [courtCode, setCourtCode] = useState("");
  const [filingDate, setFilingDate] = useState("");
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
      toast.error(e?.response?.data?.error?.message || "Could not create case.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const submit = (e) => {
    e.preventDefault();
    mutate({
      title,
      description: description || null,
      case_type: caseType,
      court_code: courtCode || null,
      filing_date: filingDate || null,
      client_email: clientEmail.trim() || null,
    });
  };

  return (
    <section className="ds-section mb-12">
      <h2 className="ds-h3">New case</h2>
      <p className="ds-body text-ds-text-2 mt-1">
        Link a registered client by email and the case appears on their dashboard straight away.
      </p>
      <form onSubmit={submit} className="grid gap-6 sm:grid-cols-2 mt-6 max-w-[760px]">
        <div className="sm:col-span-2">
          <label htmlFor="nc-title" className="ds-label">Title</label>
          <input id="nc-title" placeholder="e.g. Khan v. Khan — Custody" value={title} onChange={(e) => setTitle(e.target.value)}
            required minLength={3} className="ds-input" />
        </div>
        <div>
          <label htmlFor="nc-type" className="ds-label">Case type</label>
          <select id="nc-type" value={caseType} onChange={(e) => setCaseType(e.target.value)} className="ds-input">
            {Object.values(CASE_TYPES).map((t) => (
              <option key={t} value={t}>{TYPE_LABEL[t] || t}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="nc-court" className="ds-label">Court <span className="font-normal text-ds-text-2">(optional)</span></label>
          <input id="nc-court" placeholder="Family Court, Islamabad" value={courtCode} onChange={(e) => setCourtCode(e.target.value)}
            maxLength={60} className="ds-input" />
        </div>
        <div>
          <label htmlFor="nc-filed" className="ds-label">Filing date <span className="font-normal text-ds-text-2">(optional)</span></label>
          <input id="nc-filed" type="date" value={filingDate} onChange={(e) => setFilingDate(e.target.value)} className="ds-input" />
        </div>
        <div>
          <label htmlFor="nc-client" className="ds-label">Client email <span className="font-normal text-ds-text-2">(optional)</span></label>
          <input id="nc-client" type="email" placeholder="client@example.com" value={clientEmail}
            onChange={(e) => setClientEmail(e.target.value)} className="ds-input" />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="nc-desc" className="ds-label">Case summary <span className="font-normal text-ds-text-2">(optional)</span></label>
          <textarea id="nc-desc" value={description} onChange={(e) => setDescription(e.target.value)} rows={4}
            maxLength={4000} className="ds-input py-3" placeholder="Brief summary of the matter…" />
        </div>
        <div className="sm:col-span-2 flex items-center gap-3">
          <button type="submit" disabled={isPending || title.trim().length < 3} className="ds-btn-primary">
            {isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Creating" /> : "Create case"}
          </button>
          <button type="button" onClick={onDone} className="ds-btn-secondary">Cancel</button>
        </div>
      </form>
    </section>
  );
}
