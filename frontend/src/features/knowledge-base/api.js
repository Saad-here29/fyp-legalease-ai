import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

// Read-only knowledge base (kb-v2): laws, their section records, downloads.
const blob = (url) => client.get(url, { responseType: "blob" }).then((r) => r.data);

export const kbApi = {
  stats: () => client.get(ENDPOINTS.kb.stats).then((r) => r.data),
  documents: (params) => client.get(ENDPOINTS.kb.documents, { params }).then((r) => r.data),
  document: (id) => client.get(ENDPOINTS.kb.document(id)).then((r) => r.data),
  sections: (id) => client.get(ENDPOINTS.kb.sections(id)).then((r) => r.data),
  record: (recordId) => client.get(ENDPOINTS.kb.record(recordId)).then((r) => r.data),
  downloadJson: (id) => blob(ENDPOINTS.kb.download(id)),
  original: (id) => blob(ENDPOINTS.kb.original(id)),
};

// Save a Blob under a file name (the API needs the auth cookie, so a plain
// link can't be used for every browser).
export function saveBlob(data, filename) {
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function openBlob(data) {
  const url = URL.createObjectURL(data);
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
