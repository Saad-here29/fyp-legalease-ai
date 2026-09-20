import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Upload, FileText, Loader2, ScanLine, AlertCircle, Bookmark, CheckCircle2 } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { useAuthStore } from "@/store/authStore";
import { ROLES } from "@/constants";
import { documentsApi } from "./api";
import { casesApi } from "@/features/case-management/api";
import { cnInput } from "@/lib/formStyles";

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
      toast.error(e?.response?.data?.error?.message || "Upload failed.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const onFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadMutation.mutate(file);
    e.target.value = "";
  };

  return (
    <AppShell
      title="Documents & OCR"
      subtitle={
        isLawyer
          ? "Upload, extract text via OCR, and attach to one of your cases"
          : "Upload your case-related documents — your counsel will see them"
      }
    >
      <div className="grid gap-10 lg:grid-cols-2">
        <PanelCard title="Upload" description="Supports PDF, DOCX, TXT, PNG, JPG. Up to 20 MB.">
          <label
            htmlFor="doc-upload"
            className="block cursor-pointer border border-hairline hover:border-ink-text hover:bg-ink-text/[0.02] p-10 text-center transition-colors"
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
                <Loader2 className="h-6 w-6 animate-spin text-ink-muted" />
                <p className="text-sm text-ink-muted">Uploading and running OCR…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="h-6 w-6 text-ink-muted" />
                <p className="text-sm text-ink-text">Click to upload</p>
                <p className="text-xs text-ink-muted">or drag and drop your legal document</p>
              </div>
            )}
          </label>

          {uploadMutation.isError && (
            <div className="mt-4 flex items-start gap-2 text-sm">
              <AlertCircle className="h-4 w-4 text-brick shrink-0 mt-0.5" />
              <p className="text-brick">
                {uploadMutation.error?.response?.data?.error?.message ||
                  "Upload failed. Check file size and type."}
              </p>
            </div>
          )}
        </PanelCard>

        {doc && (
          <PanelCard title="Extracted document" description={doc.filename}>
            <div className="grid grid-cols-3 mb-4">
              <Stat label="Type" value={doc.document_type} />
              <Stat label="Size" value={formatBytes(doc.size_bytes)} />
              <Stat
                label="Text"
                value={`${(doc.extracted_text?.length || 0).toLocaleString()} chars`}
                last
              />
            </div>

            <div className="border border-hairline-subtle p-4 max-h-96 overflow-y-auto">
              {doc.extracted_text ? (
                <pre className="text-xs whitespace-pre-wrap text-ink-muted">
                  {doc.extracted_text}
                </pre>
              ) : (
                <div className="flex items-start gap-2 text-sm text-ink-muted">
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

      {doc && isLawyer && <SaveToCasePanel doc={doc} onAttached={setDoc} />}

      {!doc && (
        <div className="mt-10 text-center py-8 text-sm text-ink-muted">
          <FileText className="h-7 w-7 mx-auto mb-3 text-ink-muted/50" />
          Upload a document to extract its text via OCR
        </div>
      )}
    </AppShell>
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
      toast.error(e?.response?.data?.error?.message || "Could not attach to case.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const openCases = (cases || []).filter((c) => c.status !== "closed");
  const alreadyAttached = !!doc.case_id;

  return (
    <div className="mt-10">
      <PanelCard
        title="Save to a case"
        description={
          alreadyAttached
            ? "This document is already attached to a case."
            : "Attach this OCR extraction to one of your open cases — it appears on the case timeline."
        }
      >
        {alreadyAttached ? (
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="h-4 w-4 text-status-active" />
            <span className="text-ink-text">Linked to case</span>
            <span className="text-xs text-ink-muted">{doc.case_id?.slice(0, 8)}</span>
          </div>
        ) : openCases.length === 0 ? (
          <p className="text-sm text-ink-muted">
            You don't have any open cases. Create one first from the Cases tab,
            then come back to attach this document.
          </p>
        ) : (
          <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 max-w-2xl">
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className={cnInput(false, "flex-1")}
            >
              <option value="">Select a case...</option>
              {openCases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} · {c.status.replace("_", " ")}
                </option>
              ))}
            </select>
            <AppButton
              disabled={!selectedCaseId || attachMutation.isPending}
              onClick={() => attachMutation.mutate(selectedCaseId)}
              className="shrink-0"
            >
              {attachMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Bookmark className="h-4 w-4" />
                  Save to case
                </>
              )}
            </AppButton>
          </div>
        )}
      </PanelCard>
    </div>
  );
}

function Stat({ label, value, last = false }) {
  return (
    <div className={`px-4 first:pl-0 py-1 ${last ? "" : "border-r border-hairline"}`}>
      <div className="text-xs text-ink-muted">{label}</div>
      <div className="text-sm font-medium text-ink-text mt-1 truncate">{value}</div>
    </div>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
