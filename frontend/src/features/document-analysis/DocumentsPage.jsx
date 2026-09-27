import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Upload, FileText, Loader2, ScanLine, AlertCircle, Check, ChevronRight } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES } from "@/constants";
import { documentsApi } from "./api";
import AnalysisResults from "./AnalysisResults";
import { casesApi } from "@/features/case-management/api";

// Documents — design system v1, per the Document Analysis mockup
// (docs/design_reference page 12): upload strip, document header with its
// status and one primary action, then AI summary | extracted data.
// Adapted to what exists: no "View original" (no download endpoint), no
// breadcrumb or document list (one document per visit), no page references.

const ACCEPT = ".pdf,.docx,.txt,.png,.jpg,.jpeg";

export default function DocumentsPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [doc, setDoc] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  const uploadMutation = useMutation({
    mutationFn: (file) => documentsApi.upload(file),
    onSuccess: (data) => {
      setDoc(data);
      setAnalysis(null);
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

  const analyzeMutation = useMutation({
    mutationFn: (id) => documentsApi.analyze(id),
    onSuccess: (data) => {
      setAnalysis(data);
      toast.success("Analysis complete.", {
        description: data.ner_available
          ? `${data.parties.length} parties, ${data.dates.length} dates, ${data.references.length} references found`
          : "Summary ready — entity extraction unavailable on this server.",
      });
    },
    onError: (e) => {
      toast.error(e?.response?.data?.error?.message || "Analysis failed.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const analysed = !!analysis && analysis.document_id === doc?.id;

  return (
    <AppShell
      title="Documents"
      subtitle={
        isLawyer
          ? "Upload a document to extract its text, analyse it and attach it to a case"
          : "Upload your case-related documents and get a plain-language summary"
      }
    >
      <UploadStrip
        busy={uploadMutation.isPending}
        onFile={(file) => uploadMutation.mutate(file)}
        again={!!doc}
      />
      {uploadMutation.isError && (
        <ErrorLine>
          {uploadMutation.error?.response?.data?.error?.message || "Upload failed. Check file size and type."}
        </ErrorLine>
      )}

      {doc && (
        <section className="mt-12">
          <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-5">
            <div className="min-w-0">
              <h2 className="ds-h2 break-words">{doc.filename}</h2>
              <p className="ds-meta mt-3 flex flex-wrap items-center gap-x-2 gap-y-1">
                <FileText className="h-4 w-4" aria-hidden="true" />
                <span>{String(doc.file_type).toUpperCase()}</span>·<span>{formatBytes(doc.size_bytes)}</span>·
                <span>{(doc.extracted_text?.length || 0).toLocaleString()} characters extracted</span>·
                <span>Uploaded {new Date(doc.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span>
                {analysed ? (
                  <span className="ds-tag-pass h-7 ml-2">
                    <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
                    Analysed
                  </span>
                ) : (
                  <span className="ds-tag-neutral h-7 ml-2">Not analysed</span>
                )}
              </p>
            </div>
            <button
              onClick={() => analyzeMutation.mutate(doc.id)}
              disabled={!doc.extracted_text || analyzeMutation.isPending}
              title={doc.extracted_text ? undefined : "No text to analyse in this file"}
              // One primary per view: Analyse until done, then Save to case takes over.
              className={analysed ? "ds-btn-secondary" : "ds-btn-primary"}
            >
              {analyzeMutation.isPending ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                  Analysing…
                </>
              ) : analysed ? (
                "Re-analyse"
              ) : (
                "Analyse document"
              )}
            </button>
          </div>

          {isLawyer && <SaveToCase doc={doc} onAttached={setDoc} primary={analysed} />}

          <details className="group mt-8 border-t border-ds-rule">
            <summary
              className="cursor-pointer list-none min-h-[48px] flex items-center gap-2 font-ds-sans font-semibold text-[16px] text-ds-text
                focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink [&::-webkit-details-marker]:hidden"
            >
              <ChevronRight className="h-5 w-5 transition-transform group-open:rotate-90" aria-hidden="true" />
              Extracted text
            </summary>
            <div className="bg-ds-sheet border border-ds-rule rounded-ds p-5 max-h-96 overflow-y-auto">
              {doc.extracted_text ? (
                <pre className="font-ds-sans text-[14px] leading-[22px] whitespace-pre-wrap text-ds-text-2">
                  {doc.extracted_text}
                </pre>
              ) : (
                <div className="flex items-start gap-3 ds-body text-ds-text-2">
                  <ScanLine className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
                  <div>
                    <p>No text extracted from this file.</p>
                    <p className="ds-meta mt-1">
                      Likely a scanned or image-only PDF. OCR for these needs Tesseract OCR and Poppler installed on
                      the server.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </details>
        </section>
      )}

      {analyzeMutation.isPending && (
        <p className="mt-12 flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Summarising and extracting entities — this usually takes 10–20 seconds…
        </p>
      )}
      {analyzeMutation.isError && !analyzeMutation.isPending && (
        <ErrorLine>
          {analyzeMutation.error?.response?.data?.error?.message || "Analysis failed. Please try again in a minute."}
        </ErrorLine>
      )}

      {analysed && !analyzeMutation.isPending && <AnalysisResults analysis={analysis} />}
    </AppShell>
  );
}

function UploadStrip({ busy, onFile, again }) {
  const [over, setOver] = useState(false);
  const take = (file) => file && !busy && onFile(file);

  return (
    <label
      htmlFor="doc-upload"
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        take(e.dataTransfer.files?.[0]);
      }}
      className={`flex flex-wrap items-center justify-between gap-x-6 gap-y-2 min-h-[72px] px-6 py-4 border border-dashed rounded-ds
        cursor-pointer transition-colors focus-within:outline focus-within:outline-2 focus-within:outline-ds-ink ${
        over ? "border-ds-ink bg-ds-sheet" : "border-[#C7BBA5] hover:bg-ds-sheet/60"
      }`}
    >
      <input
        id="doc-upload"
        type="file"
        accept={ACCEPT}
        className="sr-only"
        disabled={busy}
        onChange={(e) => {
          take(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <span className="flex items-center gap-4 ds-body">
        {busy ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin text-ds-text-2" aria-hidden="true" />
            Uploading and extracting text…
          </>
        ) : (
          <>
            <Upload className="h-5 w-5 text-ds-text-2" aria-hidden="true" />
            <span>
              {again ? "Drop another file to analyse, or " : "Drop a document to analyse, or "}
              <span className="ds-link">browse</span>
            </span>
          </>
        )}
      </span>
      <span className="ds-meta">PDF, DOCX, TXT, PNG, JPG · up to 20 MB</span>
    </label>
  );
}

function SaveToCase({ doc, onAttached, primary }) {
  const [selectedCaseId, setSelectedCaseId] = useState("");

  const { data: cases } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });

  const attachMutation = useMutation({
    mutationFn: (caseId) => documentsApi.attachToCase(doc.id, caseId),
    onSuccess: (updated) => {
      onAttached(updated);
      toast.success("Attached to case.", { description: "This document now appears on the case timeline." });
    },
    onError: (e) => {
      toast.error(e?.response?.data?.error?.message || "Could not attach to case.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const openCases = (cases || []).filter((c) => c.status !== "closed");
  const attachedTo = doc.case_id && (cases || []).find((c) => c.id === doc.case_id);

  return (
    <div className="mt-6 pt-6 border-t border-ds-rule">
      {doc.case_id ? (
        <p className="flex items-center gap-2 ds-body">
          <span className="ds-tag-pass h-7">
            <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
            Saved to case
          </span>
          <span className="font-semibold">{attachedTo?.title || doc.case_id.slice(0, 8)}</span>
        </p>
      ) : openCases.length === 0 ? (
        <p className="ds-body text-ds-text-2">
          To save this document to a case, first create one from the Cases page.
        </p>
      ) : (
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 max-w-2xl">
          <div className="flex-1">
            <label htmlFor="attach-case" className="ds-label">Save to a case</label>
            <select
              id="attach-case"
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className="ds-input"
            >
              <option value="">Select a case…</option>
              {openCases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} · {c.status.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <button
            disabled={!selectedCaseId || attachMutation.isPending}
            onClick={() => attachMutation.mutate(selectedCaseId)}
            className={`${primary ? "ds-btn-primary" : "ds-btn-secondary"} min-h-[48px] shrink-0`}
          >
            {attachMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Saving" /> : "Save to case"}
          </button>
        </div>
      )}
    </div>
  );
}

function ErrorLine({ children }) {
  return (
    <p className="mt-4 flex items-start gap-2 ds-body text-ds-seal" role="alert">
      <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
      {children}
    </p>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
