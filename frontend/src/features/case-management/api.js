import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const casesApi = {
  list: () => client.get(ENDPOINTS.cases.list).then((r) => r.data),
  stats: () => client.get(ENDPOINTS.cases.stats).then((r) => r.data),
  get: (id) => client.get(ENDPOINTS.cases.byId(id)).then((r) => r.data),
  timeline: (id) =>
    client.get(ENDPOINTS.cases.timeline(id)).then((r) => r.data),
  listDocuments: (id) =>
    client.get(ENDPOINTS.cases.documents(id)).then((r) => r.data),
  create: (payload) =>
    client.post(ENDPOINTS.cases.create, payload).then((r) => r.data),
  assignClientByEmail: (id, client_email) =>
    client
      .post(ENDPOINTS.cases.assignClient(id), { client_email })
      .then((r) => r.data),
  updateStatus: (id, status) =>
    client
      .patch(ENDPOINTS.cases.updateStatus(id), { status })
      .then((r) => r.data),
  saveResearch: (id, payload) =>
    client.post(ENDPOINTS.cases.saveResearch(id), payload).then((r) => r.data),
};
