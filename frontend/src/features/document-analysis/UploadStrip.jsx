import { useState } from "react";
import { Upload, Loader2 } from "lucide-react";

// Dashed upload strip with working drag-and-drop (design page 12). Shared
// by the Documents page and a case's Documents tab.

const ACCEPT = ".pdf,.docx,.txt,.png,.jpg,.jpeg";

export default function UploadStrip({ busy, onFile, again = false, id = "doc-upload", idleText }) {
  const [over, setOver] = useState(false);
  const take = (file) => file && !busy && onFile(file);

  return (
    <label
      htmlFor={id}
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
        id={id}
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
              {idleText || (again ? "Drop another file to analyse, or " : "Drop a document to analyse, or ")}
              <span className="ds-link">browse</span>
            </span>
          </>
        )}
      </span>
      <span className="ds-meta">PDF, DOCX, TXT, PNG, JPG · up to 20 MB</span>
    </label>
  );
}
