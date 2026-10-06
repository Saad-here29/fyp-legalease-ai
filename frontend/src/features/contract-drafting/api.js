import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const contractsApi = {
  list: () => client.get(ENDPOINTS.contracts.list).then((r) => r.data),
  get: (id) => client.get(ENDPOINTS.contracts.byId(id)).then((r) => r.data),
  versions: (id) =>
    client.get(ENDPOINTS.contracts.versions(id)).then((r) => r.data),
  draft: (payload) =>
    client.post(ENDPOINTS.contracts.draft, payload).then((r) => r.data),
  // Save edited text as the next version; the response carries its compliance result.
  edit: (id, content) =>
    client.post(ENDPOINTS.contracts.versions(id), { content }).then((r) => r.data),
  checkCompliance: (id, versionNumber) =>
    client
      .post(ENDPOINTS.contracts.checkCompliance(id), {
        version_number: versionNumber ?? null,
      })
      .then((r) => r.data),
};
