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
  get: (id) => client.get(ENDPOINTS.documents.byId(id)).then((r) => r.data),
  analyze: (id) =>
    client.post(ENDPOINTS.documents.analyze(id)).then((r) => r.data),
  attachToCase: (id, case_id) =>
    client
      .post(`/documents/${id}/attach`, { case_id })
      .then((r) => r.data),
};
