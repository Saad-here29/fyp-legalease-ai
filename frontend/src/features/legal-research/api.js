import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const researchApi = {
  search: (payload) =>
    client.post(ENDPOINTS.research.search, payload).then((r) => r.data),
  get: (id) => client.get(ENDPOINTS.research.byId(id)).then((r) => r.data),
  analyze: ({ text, source, user_query }) =>
    client
      .post("/research/analyze", { text, source, user_query })
      .then((r) => r.data),
};
