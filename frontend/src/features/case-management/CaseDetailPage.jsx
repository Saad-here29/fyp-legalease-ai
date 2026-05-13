import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  ArrowRight,
  Upload,
  FileText,
  UserPlus,
  Gavel,
  CheckCircle2,
  Clock,
  BookOpen,
  ScanLine,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "./api";
import { documentsApi } from "@/features/document-analysis/api";

const NEXT_STATUS = {
  CREATED: "ASSIGNED",
  ASSIGNED: "IN_PROGRESS",
  IN_PROGRESS: "HEARING_SCHEDULED",
  HEARING_SCHEDULED: "CLOSED",
  CLOSED: null,
};

const STATUS_VARIANT = {
  CREATED: "outline",
  ASSIGNED: "secondary",
  IN_PROGRESS: "default",
  HEARING_SCHEDULED: "gold",
  CLOSED: "success",
};

const TIMELINE_ICON = {
  CREATED: FileText,
  STATUS: Gavel,
  CLIENT_ASSIGNED: UserPlus,
  DOCUMENT: Upload,
  NOTE: BookOpen,
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
      <DashboardLayout title="Case">
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading case...
        </div>
      </DashboardLayout>
    );
  }

  if (caseQuery.isError) {
    return (
      <DashboardLayout title="Case">
        <PanelCard>
          <div className="flex items-start gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">
                {caseQuery.error?.response?.data?.error?.message ||
                  "Could not load this case."}
              </p>
              <Link to={ROUTES.CASES} className="text-sm text-accent hover:underline mt-2 inline-block">
                ← Back to all cases
              </Link>
            </div>
          </div>
        </PanelCard>
      </DashboardLayout>
    );
  }

  const nextStatus = NEXT_STATUS[c.status];

  return (
    <DashboardLayout title={c.title} subtitle={`${c.case_type} · ${c.id.slice(0, 8)}`}>
      <Link
        to={ROUTES.CASES}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        All cases
      </Link>

      {/* Hero: status + actions */}
      <PanelCard className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <Badge variant={STATUS_VARIANT[c.status]} className="text-[10px] uppercase tracking-wider">
                {c.status.replace("_", " ")}
              </Badge>
              {c.court_code && (
                <span className="text-sm text-muted-foreground">
                  {c.court_code}
                </span>
              )}
              {c.filing_date && (
                <span className="text-sm text-muted-foreground">
                  · Filed {c.filing_date}
                </span>
              )}
            </div>
            {c.description && (
              <p className="text-sm text-muted-foreground mt-3 max-w-2xl">
                {c.description}
              </p>
            )}
          </div>
          {isLawyer && nextStatus && (
            <Button
              variant="gold"
              disabled={advanceStatus.isPending}
              onClick={() => advanceStatus.mutate(nextStatus)}
            >
              {advanceStatus.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Advance to {nextStatus.replace("_", " ")}
                  <ArrowRight className="h-4 w-4 ml-1" />
                </>
              )}
            </Button>
          )}
        </div>
      </PanelCard>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: parties + (lawyer) actions */}
        <div className="space-y-6">
          <PanelCard title="Parties">
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Lawyer
                </div>
                <div className="font-semibold">{c.lawyer_name || "—"}</div>
                <div className="text-xs text-muted-foreground">{c.lawyer_email || ""}</div>
              </div>
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Client
                </div>
                {c.client_email ? (
                  <>
                    <div className="font-semibold">{c.client_name || "—"}</div>
                    <div className="text-xs text-muted-foreground">{c.client_email}</div>
                  </>
                ) : (
                  <div className="text-xs text-muted-foreground italic">
                    Not yet assigned
                  </div>
                )}
              </div>
            </div>

            {isLawyer && (
              <div className="mt-4 pt-4 border-t border-border/40 space-y-2">
                <Label className="text-xs">
                  {c.client_email ? "Reassign client by email" : "Assign client by email"}
                </Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="client@example.com"
                    value={assignEmail}
                    onChange={(e) => setAssignEmail(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={assignClient.isPending || !assignEmail.trim()}
                    onClick={() => assignClient.mutate(assignEmail.trim())}
                  >
                    {assignClient.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <UserPlus className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
              </div>
            )}
          </PanelCard>

          {isLawyer && (
            <PanelCard title="Upload document" description="Linked to this case">
              <label
                htmlFor="case-doc-upload"
                className="block cursor-pointer rounded-lg border-2 border-dashed border-border/60 bg-background/30 p-6 text-center hover:border-accent/50 hover:bg-accent/5 transition-colors"
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
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Uploading + OCR...
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="h-6 w-6 text-accent" />
                    <p className="text-sm font-medium">Choose a file</p>
                    <p className="text-xs text-muted-foreground">
                      PDF / DOCX / image — auto-OCR + AI analysis
                    </p>
                  </div>
                )}
              </label>
            </PanelCard>
          )}
        </div>

        {/* Middle column: timeline */}
        <PanelCard title="Timeline" description="Every event on this case">
          {timelineQuery.isLoading && <Spinner />}
          {timelineQuery.data && timelineQuery.data.length === 0 && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No activity yet.
            </p>
          )}
          {timelineQuery.data && timelineQuery.data.length > 0 && (
            <ol className="relative border-l border-border/40 ml-2 space-y-5">
              {timelineQuery.data.map((entry, i) => {
                const Icon = TIMELINE_ICON[entry.kind] || Clock;
                return (
                  <li key={i} className="ml-6">
                    <div className="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-accent/15 border border-accent/30">
                      <Icon className="h-3 w-3 text-accent" />
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                    <div className="font-semibold text-sm mt-0.5">{entry.title}</div>
                    {entry.description && (
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {entry.description}
                      </div>
                    )}
                    {entry.actor_name && (
                      <div className="text-[10px] text-muted-foreground mt-1 italic">
                        by {entry.actor_name}
                      </div>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
        </PanelCard>

        {/* Right column: documents */}
        <PanelCard title="Documents" description={`${c.document_count} attached`}>
          {documentsQuery.isLoading && <Spinner />}
          {documentsQuery.data && documentsQuery.data.length === 0 && (
            <div className="text-center py-6">
              <FileText className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No documents yet.</p>
              {isLawyer && (
                <p className="text-xs text-muted-foreground mt-1">
                  Upload one from the left panel.
                </p>
              )}
            </div>
          )}
          {documentsQuery.data && documentsQuery.data.length > 0 && (
            <ul className="space-y-3">
              {documentsQuery.data.map((d) => (
                <DocumentItem key={d.id} doc={d} />
              ))}
            </ul>
          )}
        </PanelCard>
      </div>
    </DashboardLayout>
  );
}

function DocumentItem({ doc }) {
  const [showText, setShowText] = useState(false);

  return (
    <motion.li
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-border/40 bg-background/30 p-3"
    >
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-accent shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold truncate">{doc.filename}</div>
          <div className="text-[10px] text-muted-foreground">
            {doc.file_type} · {doc.document_type}
          </div>
        </div>
      </div>

      {doc.extracted_text && (
        <button
          onClick={() => setShowText((v) => !v)}
          className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-accent hover:underline"
        >
          <ScanLine className="h-3 w-3" />
          {showText ? "Hide" : "View"} extracted text ({doc.extracted_text.length} chars)
        </button>
      )}

      {showText && (
        <pre className="mt-2 text-[10px] whitespace-pre-wrap font-mono text-muted-foreground max-h-64 overflow-y-auto scrollbar-thin rounded bg-background/50 p-2 border border-border/40">
          {doc.extracted_text}
        </pre>
      )}
    </motion.li>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-6 gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      Loading...
    </div>
  );
}
