import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  AlertCircle,
  Upload,
  FileText,
  UserPlus,
  Gavel,
  ScanLine,
} from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "./api";
import { documentsApi } from "@/features/document-analysis/api";
import { cnInput } from "@/lib/formStyles";

const NEXT_STATUS = {
  created: "assigned",
  assigned: "in_progress",
  in_progress: "hearing_scheduled",
  hearing_scheduled: "closed",
  closed: null,
};

const STATUS_META = {
  created: { dot: "bg-status-pending", label: "Created" },
  assigned: { dot: "bg-status-pending", label: "Assigned" },
  in_progress: { dot: "bg-status-active", label: "In progress" },
  hearing_scheduled: { dot: "bg-status-active", label: "Hearing scheduled" },
  closed: { dot: "bg-ink-muted", label: "Closed" },
};

const TIMELINE_ICON = {
  CREATED: FileText,
  STATUS: Gavel,
  CLIENT_ASSIGNED: UserPlus,
  DOCUMENT: Upload,
  NOTE: FileText,
};

export default function CaseDetailPage() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const qc = useQueryClient();

  const caseQuery = useQuery({
    queryKey: ["case", id],
    queryFn: () => casesApi.get(id),
  });
  const timelineQuery = useQuery({
    queryKey: ["case-timeline", id],
    queryFn: () => casesApi.timeline(id),
  });
  const documentsQuery = useQuery({
    queryKey: ["case-documents", id],
    queryFn: () => casesApi.listDocuments(id),
  });

  const c = caseQuery.data;

  const advanceStatus = useMutation({
    mutationFn: (status) => casesApi.updateStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] });
      qc.invalidateQueries({ queryKey: ["case-timeline", id] });
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["case-stats"] });
      toast.success("Status updated.");
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not update status.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const assignClient = useMutation({
    mutationFn: (email) => casesApi.assignClientByEmail(id, email),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] });
      qc.invalidateQueries({ queryKey: ["case-timeline", id] });
      toast.success("Client linked.");
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not link client.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const uploadDocument = useMutation({
    mutationFn: (file) => documentsApi.upload(file, { caseId: id }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] });
      qc.invalidateQueries({ queryKey: ["case-timeline", id] });
      qc.invalidateQueries({ queryKey: ["case-documents", id] });
      toast.success("Document uploaded and linked to this case.");
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Upload failed.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const [assignEmail, setAssignEmail] = useState("");

  if (caseQuery.isLoading) {
    return (
      <AppShell title="Case">
        <div className="flex items-center justify-center gap-2 py-12 text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading case…
        </div>
      </AppShell>
    );
  }

  if (caseQuery.isError) {
    return (
      <AppShell title="Case">
        <div className="max-w-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-ink-text">
                {caseQuery.error?.response?.data?.error?.message ||
                  "Could not load this case."}
              </p>
              <Link
                to={ROUTES.CASES}
                className="text-sm text-brick hover:underline underline-offset-2 mt-2 inline-block"
              >
                ← Back to all cases
              </Link>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  const nextStatus = NEXT_STATUS[c.status];
  const statusMeta = STATUS_META[c.status] || {};

  return (
    <AppShell title={c.title} subtitle={`${c.case_type} · ${c.id.slice(0, 8)}`}>
      <Link
        to={ROUTES.CASES}
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink-text mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        All cases
      </Link>

      <div className="pb-6 mb-8 border-b border-hairline">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap text-sm text-ink-muted">
              <span className="inline-flex items-center gap-1.5">
                <span className={`h-1.5 w-1.5 rounded-full ${statusMeta.dot || "bg-ink-muted"}`} />
                {statusMeta.label || c.status}
              </span>
              {c.court_code && <span>· {c.court_code}</span>}
              {c.filing_date && <span>· Filed {c.filing_date}</span>}
            </div>
            {c.description && (
              <p className="text-sm text-ink-muted mt-3 max-w-2xl">{c.description}</p>
            )}
          </div>
          {isLawyer && nextStatus && (
            <AppButton
              disabled={advanceStatus.isPending}
              onClick={() => advanceStatus.mutate(nextStatus)}
              className="shrink-0"
            >
              {advanceStatus.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Advance to {nextStatus.replace("_", " ")}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </AppButton>
          )}
        </div>
      </div>

      <div className="grid gap-10 lg:grid-cols-3">
        <div className="space-y-10">
          <Panel title="Parties">
            <div className="space-y-4">
              <div className="pb-4 border-b border-hairline-subtle">
                <div className="text-xs text-ink-muted mb-1">Lawyer</div>
                <div className="text-sm font-medium text-ink-text">{c.lawyer_name || "—"}</div>
                <div className="text-xs text-ink-muted">{c.lawyer_email || ""}</div>
              </div>
              <div>
                <div className="text-xs text-ink-muted mb-1">Client</div>
                {c.client_email ? (
                  <>
                    <div className="text-sm font-medium text-ink-text">{c.client_name || "—"}</div>
                    <div className="text-xs text-ink-muted">{c.client_email}</div>
                  </>
                ) : (
                  <div className="text-sm text-ink-muted">Not yet assigned</div>
                )}
              </div>
            </div>

            {isLawyer && (
              <div className="mt-5 pt-5 border-t border-hairline-subtle">
                <label className="block text-xs text-ink-muted mb-1.5">
                  {c.client_email ? "Reassign client by email" : "Assign client by email"}
                </label>
                <div className="flex items-end gap-2">
                  <input
                    type="email"
                    placeholder="client@example.com"
                    value={assignEmail}
                    onChange={(e) => setAssignEmail(e.target.value)}
                    className={cnInput(false, "flex-1")}
                  />
                  <button
                    disabled={assignClient.isPending || !assignEmail.trim()}
                    onClick={() => assignClient.mutate(assignEmail.trim())}
                    className="h-9 w-9 flex items-center justify-center text-ink-muted hover:text-ink-text disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
                    aria-label="Assign"
                  >
                    {assignClient.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <UserPlus className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            )}
          </Panel>

          {isLawyer && (
            <Panel title="Upload document" description="Linked to this case">
              <label
                htmlFor="case-doc-upload"
                className="block cursor-pointer border border-hairline hover:border-ink-text hover:bg-ink-text/[0.02] p-6 text-center transition-colors"
              >
                <input
                  id="case-doc-upload"
                  type="file"
                  accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) uploadDocument.mutate(file);
                    e.target.value = "";
                  }}
                  disabled={uploadDocument.isPending}
                />
                {uploadDocument.isPending ? (
                  <div className="flex items-center justify-center gap-2 text-sm text-ink-muted">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Uploading + OCR…
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="h-5 w-5 text-ink-muted" />
                    <p className="text-sm text-ink-text">Choose a file</p>
                    <p className="text-xs text-ink-muted">
                      PDF / DOCX / image — auto-OCR + AI analysis
                    </p>
                  </div>
                )}
              </label>
            </Panel>
          )}
        </div>

        <Panel title="Timeline" description="Every event on this case">
          {timelineQuery.isLoading ? (
            <LoadingBlock label="Loading…" small />
          ) : timelineQuery.data?.length === 0 ? (
            <p className="text-sm text-ink-muted py-4 text-center">No activity yet.</p>
          ) : (
            <ul>
              {(timelineQuery.data || []).map((entry, i) => {
                const Icon = TIMELINE_ICON[entry.kind] || Gavel;
                return (
                  <li key={i} className="py-3.5 border-b border-hairline-subtle last:border-0">
                    <div className="text-xs text-ink-muted">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Icon className="h-3.5 w-3.5 text-ink-muted shrink-0" />
                      <span className="text-sm font-medium text-ink-text">{entry.title}</span>
                    </div>
                    {entry.description && (
                      <div className="text-xs text-ink-muted mt-0.5 pl-5">{entry.description}</div>
                    )}
                    {entry.actor_name && (
                      <div className="text-xs text-ink-muted/70 mt-0.5 pl-5">
                        by {entry.actor_name}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel title="Documents" description={`${c.document_count} attached`}>
          {documentsQuery.isLoading ? (
            <LoadingBlock label="Loading…" small />
          ) : documentsQuery.data?.length === 0 ? (
            <div className="text-center py-6">
              <FileText className="h-7 w-7 text-ink-muted/50 mx-auto mb-2" />
              <p className="text-sm text-ink-muted">No documents yet.</p>
              {isLawyer && (
                <p className="text-xs text-ink-muted mt-1">Upload one from the left panel.</p>
              )}
            </div>
          ) : (
            <ul>
              {(documentsQuery.data || []).map((d) => (
                <DocumentItem key={d.id} doc={d} />
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </AppShell>
  );
}

function DocumentItem({ doc }) {
  const [showText, setShowText] = useState(false);

  return (
    <li className="py-3.5 border-b border-hairline-subtle last:border-0">
      <div className="flex items-center gap-2.5">
        <FileText className="h-4 w-4 text-ink-muted shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-ink-text truncate">{doc.filename}</div>
          <div className="text-xs text-ink-muted">
            {doc.file_type} · {doc.document_type}
          </div>
        </div>
      </div>

      {doc.extracted_text && (
        <button
          onClick={() => setShowText((v) => !v)}
          className="mt-2 ml-6 inline-flex items-center gap-1 text-xs text-brick hover:underline underline-offset-2"
        >
          <ScanLine className="h-3 w-3" />
          {showText ? "Hide" : "View"} extracted text ({doc.extracted_text.length} chars)
        </button>
      )}

      {showText && (
        <pre className="mt-2 ml-6 text-xs whitespace-pre-wrap text-ink-muted max-h-64 overflow-y-auto p-3 border border-hairline-subtle">
          {doc.extracted_text}
        </pre>
      )}
    </li>
  );
}

function Panel({ title, description, children }) {
  return (
    <section>
      {title && <h2 className="font-editorial text-xl text-ink-text mb-1">{title}</h2>}
      {description && <p className="text-sm text-ink-muted mb-2">{description}</p>}
      <div className="border-t border-hairline pt-1 mt-3">{children}</div>
    </section>
  );
}

function LoadingBlock({ label, small = false }) {
  return (
    <div className={`flex items-center justify-center gap-2 text-ink-muted ${small ? "py-6" : "py-12"}`}>
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
