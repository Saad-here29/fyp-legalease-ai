import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const documentsApi = {
  upload: (file, { caseId, documentType } = {}) => {
    const form = new FormData();
    form.append("file", file);
    if (caseId) form.append("case_id", caseId);
    if (documentType) form.append("document_type", documentType);
    return client
      .post(ENDPOINTS.documents.upload, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  capabilities: () => client.get(ENDPOINTS.documents.capabilities).then((r) => r.data),
  // With the reasoning layer a long document is analysed in several paced
  // model calls (kb-v2 C10), which can take a few minutes.
  analyze: (id) =>
    client.post(ENDPOINTS.documents.analyze(id), null, { timeout: 6 * 60 * 1000 }).then((r) => r.data),
  attachToCase: (id, case_id) =>
    client
      .post(`/documents/${id}/attach`, { case_id })
      .then((r) => r.data),
};
