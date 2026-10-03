import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertCircle, Check, ChevronRight } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "./api";
import { documentsApi } from "@/features/document-analysis/api";
import UploadStrip from "@/features/document-analysis/UploadStrip";
import { useUploadTypes } from "@/features/document-analysis/useUploadTypes";
import StatusTag from "./StatusTag";
import { STATUS, TYPE_LABEL, fmtDate, readableTimelineEntry } from "./caseMeta";

// Case detail — design system v1, per the Case detail mockup
// (docs/design_reference page 9). Adapted to what exists: no hearings,
// issues framed, next-hearing panel, research or notes tabs (none are
// built); the one primary action is the real status change, and "Add
// document" uploads straight to this case.

const NEXT_STATUS = {
  created: "assigned",
  assigned: "in_progress",
  in_progress: "hearing_scheduled",
  hearing_scheduled: "closed",
  closed: null,
};

const fmtDateTime = (v) =>
  new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function CaseDetailPage() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const qc = useQueryClient();
  const [tab, setTab] = useState("overview");

  const caseQuery = useQuery({ queryKey: ["case", id], queryFn: () => casesApi.get(id) });
  const timelineQuery = useQuery({ queryKey: ["case-timeline", id], queryFn: () => casesApi.timeline(id) });
  const documentsQuery = useQuery({ queryKey: ["case-documents", id], queryFn: () => casesApi.listDocuments(id) });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["case", id] });
    qc.invalidateQueries({ queryKey: ["case-timeline", id] });
  };
  const apiError = (fallback) => (e) =>
    toast.error(e?.response?.data?.error?.message || fallback, { description: e?.response?.data?.error?.hint });

  const advanceStatus = useMutation({
    mutationFn: (status) => casesApi.updateStatus(id, status),
    onSuccess: () => {
      refresh();
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["case-stats"] });
      toast.success("Status updated.");
    },
    onError: apiError("Could not update status."),
  });

  const { accept: uploadAccept } = useUploadTypes();
  const uploadDocument = useMutation({
    mutationFn: (file) => documentsApi.upload(file, { caseId: id }),
    onSuccess: (data) => {
      refresh();
      qc.invalidateQueries({ queryKey: ["case-documents", id] });
      setTab("documents");
      if (data.extraction_warning) {
        toast.warning("Linked to this case, but no text was extracted.", { description: data.extraction_warning });
      } else {
        toast.success("Document uploaded and linked to this case.");
      }
    },
    onError: apiError("Upload failed."),
  });

  const breadcrumb = (
    <Link to={ROUTES.CASES} className="ds-link font-medium">
      Cases
    </Link>
  );

  if (caseQuery.isLoading) {
    return (
      <AppShell eyebrow={breadcrumb} title="Case">
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Loading case…
        </p>
      </AppShell>
    );
  }
  if (caseQuery.isError) {
    return (
      <AppShell eyebrow={breadcrumb} title="Case">
        <p className="flex items-start gap-2 ds-body text-ds-seal" role="alert">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          {caseQuery.error?.response?.data?.error?.message || "Could not load this case."}
        </p>
      </AppShell>
    );
  }

  const c = caseQuery.data;
  const timeline = (timelineQuery.data || []).map(readableTimelineEntry);
  const docs = documentsQuery.data || [];
  const nextStatus = NEXT_STATUS[c.status];
  // A closed case takes no new documents.
  const canAddDocuments = isLawyer && c.status !== "closed";

  const headerActions = isLawyer && (
    <>
      {canAddDocuments && (
        <label
          className={`ds-btn-secondary cursor-pointer focus-within:outline focus-within:outline-2 focus-within:outline-ds-ink ${
            uploadDocument.isPending ? "pointer-events-none opacity-70" : ""
          }`}
        >
          <input
            type="file"
            accept={uploadAccept}
            className="sr-only"
            disabled={uploadDocument.isPending}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) uploadDocument.mutate(file);
              e.target.value = "";
            }}
          />
          {uploadDocument.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Uploading" /> : "Add document"}
        </label>
      )}
      {nextStatus && (
        <button className="ds-btn-primary" disabled={advanceStatus.isPending} onClick={() => advanceStatus.mutate(nextStatus)}>
          {advanceStatus.isPending ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-label="Updating" />
          ) : (
            `Mark as ${STATUS[nextStatus].label.toLowerCase()}`
          )}
        </button>
      )}
    </>
  );

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "timeline", label: "Timeline", count: timeline.length },
    { key: "documents", label: "Documents", count: docs.length },
  ];

  return (
    <AppShell
      eyebrow={breadcrumb}
      title={c.title}
      headerActions={headerActions}
      subtitle={
        <span className="flex flex-wrap items-center gap-x-3 gap-y-2 mt-2">
          <StatusTag status={c.status} />
          {[TYPE_LABEL[c.case_type] || c.case_type, c.court_code, c.filing_date && `Filed ${fmtDate(c.filing_date)}`,
            c.client_name && `Client: ${c.client_name}`]
            .filter(Boolean)
            .map((part, i) => (
              <span key={i} className="flex items-center gap-3">
                {i > 0 && <span aria-hidden="true">·</span>}
                {part}
              </span>
            ))}
        </span>
      }
    >
      <div role="tablist" aria-label="Case sections" className="flex flex-wrap gap-x-8 border-b border-ds-rule">
        {tabs.map((t) => {
          const active = t.key === tab;
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              onClick={() => setTab(t.key)}
              className={`min-h-[48px] -mb-px font-ds-sans text-[16px] border-b-2 transition-colors
                focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink ${
                active ? "border-ds-seal font-semibold text-ds-text" : "border-transparent text-ds-text-2 hover:text-ds-text"
              }`}
            >
              {t.label}
              {t.count != null && <span className="tabular-nums"> {t.count}</span>}
            </button>
          );
        })}
      </div>

      <div className="mt-10">
        {tab === "overview" && (
          <Overview c={c} timeline={timeline} docs={docs} isLawyer={isLawyer} onShow={setTab} onRefresh={refresh} />
        )}
        {tab === "timeline" && <Timeline entries={timeline} loading={timelineQuery.isLoading} />}
        {tab === "documents" && (
          <div>
            {canAddDocuments && (
              <div className="mb-8">
                <UploadStrip
                  id="case-doc-upload"
                  busy={uploadDocument.isPending}
                  onFile={(f) => uploadDocument.mutate(f)}
                  idleText="Drop a document to add to this case, or "
                />
              </div>
            )}
            <DocumentList docs={docs} loading={documentsQuery.isLoading} />
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Overview({ c, timeline, docs, isLawyer, onShow, onRefresh }) {
  const recent = timeline.slice(-3).reverse();
  return (
    <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_340px] items-start">
      <div className="space-y-12">
        <section>
          <h2 className="ds-h3">Case summary</h2>
          {c.description ? (
            <p className="ds-body mt-3 whitespace-pre-wrap text-[17px] leading-[28px]">{c.description}</p>
          ) : (
            <p className="ds-body text-ds-text-2 mt-3">No summary added for this case.</p>
          )}
        </section>

        <section>
          <div className="flex items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
            <h2 className="ds-h3">Recent activity</h2>
            {timeline.length > 3 && (
              <button onClick={() => onShow("timeline")} className="ds-link text-[15px]">
                All {timeline.length} events
              </button>
            )}
          </div>
          {recent.length === 0 ? (
            <p className="ds-body text-ds-text-2 py-4">No activity yet.</p>
          ) : (
            <TimelineRows entries={recent} />
          )}
        </section>
      </div>

      <aside className="space-y-10">
        <section>
          <h2 className="ds-h4 pb-3 border-b border-ds-rule">Parties</h2>
          <Person role="Lawyer" name={c.lawyer_name} email={c.lawyer_email} />
          <Person role="Client" name={c.client_email ? c.client_name : null} email={c.client_email} empty="Not yet assigned" />
          {isLawyer && <AssignClient caseId={c.id} hasClient={!!c.client_email} onDone={onRefresh} />}
        </section>

        <section>
          <div className="flex items-end justify-between gap-4 pb-3 border-b border-ds-rule">
            <h2 className="ds-h4">Documents</h2>
            {docs.length > 0 && (
              <button onClick={() => onShow("documents")} className="ds-link text-[15px]">
                All {docs.length}
              </button>
            )}
          </div>
          {docs.length === 0 ? (
            <p className="ds-body text-ds-text-2 py-4">No documents yet.</p>
          ) : (
            <ul>
              {docs.slice(0, 4).map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-3 min-h-[56px] border-b border-ds-rule">
                  <span className="ds-body truncate">{d.filename}</span>
                  <AnalysedLabel doc={d} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </aside>
    </div>
  );
}

function Person({ role, name, email, empty = "—" }) {
  return (
    <div className="py-4 border-b border-ds-rule">
      <p className="ds-meta">{role}</p>
      {name || email ? (
        <>
          <p className="font-ds-sans font-semibold text-[17px] leading-[24px] mt-0.5">{name || email}</p>
          {name && email && <p className="ds-meta">{email}</p>}
        </>
      ) : (
        <p className="ds-body text-ds-text-2 mt-0.5">{empty}</p>
      )}
    </div>
  );
}

function AssignClient({ caseId, hasClient, onDone }) {
  const [email, setEmail] = useState("");
  const assign = useMutation({
    mutationFn: (e) => casesApi.assignClientByEmail(caseId, e),
    onSuccess: () => {
      onDone();
      setEmail("");
      toast.success("Client linked.");
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not link client.", {
        description: e?.response?.data?.error?.hint,
      }),
  });
  return (
    <form
      className="pt-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (email.trim()) assign.mutate(email.trim());
      }}
    >
      <label htmlFor="assign-client" className="ds-label">
        {hasClient ? "Reassign client by email" : "Assign client by email"}
      </label>
      <div className="flex gap-2">
        <input id="assign-client" type="email" placeholder="client@example.com" value={email}
          onChange={(e) => setEmail(e.target.value)} className="ds-input" />
        <button type="submit" className="ds-btn-secondary shrink-0 min-h-[48px]" disabled={assign.isPending || !email.trim()}>
          {assign.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Linking" /> : "Link"}
        </button>
      </div>
    </form>
  );
}

function Timeline({ entries, loading }) {
  if (loading) return <p className="ds-body text-ds-text-2">Loading…</p>;
  if (entries.length === 0) return <p className="ds-body text-ds-text-2">No activity yet.</p>;
  return (
    <div className="border-t-2 border-ds-ink max-w-[860px]">
      <TimelineRows entries={[...entries].reverse()} />
    </div>
  );
}

function TimelineRows({ entries }) {
  return (
    <ul>
      {entries.map((e, i) => (
        <li key={i} className="grid sm:grid-cols-[170px_1fr] gap-x-6 gap-y-1 py-4 border-b border-ds-rule">
          <span className="font-ds-sans font-semibold text-[15px] leading-[24px] text-ds-text">{fmtDateTime(e.timestamp)}</span>
          <span className="ds-body">
            {e.title}
            {e.description && <span className="text-ds-text-2"> {e.description}</span>}
            {e.actor_name && <span className="ds-meta block mt-0.5">by {e.actor_name}</span>}
          </span>
        </li>
      ))}
    </ul>
  );
}

function AnalysedLabel({ doc }) {
  return doc.summary ? (
    <span className="inline-flex items-center gap-1 font-ds-sans font-semibold text-[14px] text-ds-pass shrink-0">
      <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
      Analysed
    </span>
  ) : (
    <span className="ds-meta shrink-0">Not analysed</span>
  );
}

function DocumentList({ docs, loading }) {
  if (loading) return <p className="ds-body text-ds-text-2">Loading…</p>;
  if (docs.length === 0) return <p className="ds-body text-ds-text-2">No documents on this case yet.</p>;
  return (
    <ul className="border-t-2 border-ds-ink max-w-[860px]">
      {docs.map((d) => (
        <DocumentRow key={d.id} doc={d} />
      ))}
    </ul>
  );
}

function DocumentRow({ doc }) {
  return (
    <li className="border-b border-ds-rule py-4">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1">
        <div className="min-w-0">
          <p className="font-ds-sans font-semibold text-[17px] leading-[24px] break-words">{doc.filename}</p>
          <p className="ds-meta">
            {String(doc.file_type).toUpperCase()} · uploaded {fmtDate(doc.created_at)}
            {doc.extracted_text ? ` · ${doc.extracted_text.length.toLocaleString()} characters` : " · no text extracted"}
          </p>
        </div>
        <AnalysedLabel doc={doc} />
      </div>
      {doc.extracted_text && (
        <details className="group mt-2">
          <summary className="cursor-pointer list-none inline-flex items-center gap-1.5 min-h-[44px] font-ds-sans font-semibold text-[15px]
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink [&::-webkit-details-marker]:hidden">
            <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90" aria-hidden="true" />
            Extracted text
          </summary>
          <pre className="bg-ds-sheet border border-ds-rule rounded-ds p-4 max-h-72 overflow-y-auto font-ds-sans text-[14px] leading-[22px] whitespace-pre-wrap text-ds-text-2">
            {doc.extracted_text}
          </pre>
        </details>
      )}
    </li>
  );
}
