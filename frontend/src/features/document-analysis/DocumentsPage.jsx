import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Upload,
  FileText,
  Loader2,
  ScanLine,
  AlertCircle,
  Bookmark,
  CheckCircle2,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { ROLES } from "@/constants";
import { documentsApi } from "./api";
import { casesApi } from "@/features/case-management/api";

export default function DocumentsPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [doc, setDoc] = useState(null);

  const uploadMutation = useMutation({
    mutationFn: (file) => documentsApi.upload(file),
    onSuccess: (data) => {
      setDoc(data);
      toast.success("Document uploaded.", {
        description: data.extracted_text
          ? `${data.extracted_text.length.toLocaleString()} characters extracted`
          : "Upload saved — no extractable text in this file.",
      });
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Upload failed.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const onFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadMutation.mutate(file);
    e.target.value = "";
  };

  return (
    <DashboardLayout
      title="Documents & OCR"
      subtitle={
        isLawyer
          ? "Upload, extract text via OCR, and attach to one of your cases"
          : "Upload your case-related documents — your counsel will see them"
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <PanelCard
          title="Upload"
          description="Supports PDF, DOCX, TXT, PNG, JPG. Up to 20 MB."
        >
          <label
            htmlFor="doc-upload"
            className="block cursor-pointer rounded-xl border-2 border-dashed border-border/60 bg-background/30 p-10 text-center hover:border-accent/50 hover:bg-accent/5 transition-colors"
          >
            <input
              id="doc-upload"
              type="file"
              accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
              className="hidden"
              onChange={onFile}
              disabled={uploadMutation.isPending}
            />
            {uploadMutation.isPending ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-accent" />
                <p className="text-sm text-muted-foreground">
                  Uploading and running OCR...
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="h-14 w-14 rounded-2xl bg-gold-gradient flex items-center justify-center">
                  <Upload className="h-6 w-6 text-legal-navy" />
                </div>
                <div>
                  <p className="font-semibold">Click to upload</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    or drag and drop your legal document
                  </p>
                </div>
              </div>
            )}
          </label>

          {uploadMutation.isError && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
              <p className="text-destructive">
                {uploadMutation.error?.response?.data?.error?.message ||
                  "Upload failed. Check file size and type."}
              </p>
            </div>
          )}
        </PanelCard>

        {doc && (
          <PanelCard
            title="Extracted document"
            description={doc.filename}
            action={
              <Badge variant="gold" className="text-[10px] uppercase tracking-wider">
                {doc.file_type}
              </Badge>
            }
          >
            <div className="grid grid-cols-3 gap-3 mb-4">
              <Stat label="Type" value={doc.document_type} />
              <Stat label="Size" value={formatBytes(doc.size_bytes)} />
              <Stat
                label="Text"
                value={`${(doc.extracted_text?.length || 0).toLocaleString()} chars`}
              />
            </div>

            <div className="rounded-lg border border-border/40 bg-background/30 p-4 max-h-96 overflow-y-auto scrollbar-thin">
              {doc.extracted_text ? (
                <pre className="text-xs whitespace-pre-wrap font-mono text-muted-foreground">
                  {doc.extracted_text}
                </pre>
              ) : (
                <div className="flex items-start gap-2 text-sm text-muted-foreground">
                  <ScanLine className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <p>No text extracted from this file.</p>
                    <p className="text-xs mt-1">
                      Likely a scanned/image-only PDF. To enable OCR for these,
                      install Tesseract OCR + Poppler on the server.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </PanelCard>
        )}
      </div>

      {/* Lawyer-only: attach the just-uploaded document to one of their cases */}
      {doc && isLawyer && <SaveToCasePanel doc={doc} onAttached={setDoc} />}

      {!doc && (
        <PanelCard className="mt-6">
          <div className="text-center py-8 text-sm text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-3 text-muted-foreground/40" />
            Upload a document to extract its text via OCR
          </div>
        </PanelCard>
      )}
    </DashboardLayout>
  );
}

function SaveToCasePanel({ doc, onAttached }) {
  const [selectedCaseId, setSelectedCaseId] = useState("");

  const { data: cases } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const attachMutation = useMutation({
    mutationFn: (caseId) => documentsApi.attachToCase(doc.id, caseId),
    onSuccess: (updated) => {
      onAttached(updated);
      toast.success("Attached to case.", {
        description: "This document now appears on the case timeline.",
      });
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not attach to case.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const openCases = (cases || []).filter((c) => c.status !== "CLOSED");
  const alreadyAttached = !!doc.case_id;

  return (
    <PanelCard
      className="mt-6"
      title="Save to a case"
      description={
        alreadyAttached
          ? "This document is already attached to a case."
          : "Attach this OCR extraction to one of your open cases — it appears on the case timeline."
      }
    >
      {alreadyAttached ? (
        <div className="flex items-center gap-2 text-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-foreground">Linked to case</span>
          <span className="text-xs font-mono text-muted-foreground">
            {doc.case_id?.slice(0, 8)}
          </span>
        </div>
      ) : openCases.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          You don't have any open cases. Create one first from the Cases tab,
          then come back to attach this document.
        </p>
      ) : (
        <div className="flex flex-col sm:flex-row gap-2 max-w-2xl">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select a case...</option>
            {openCases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title} · {c.status.replace("_", " ")}
              </option>
            ))}
          </select>
          <Button
            variant="gold"
            disabled={!selectedCaseId || attachMutation.isPending}
            onClick={() => attachMutation.mutate(selectedCaseId)}
          >
            {attachMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Bookmark className="h-4 w-4" />
                Save to case
              </>
            )}
          </Button>
        </div>
      )}
    </PanelCard>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-lg border border-border/40 bg-background/30 p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="text-sm font-semibold mt-1 truncate">{value}</div>
    </div>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
