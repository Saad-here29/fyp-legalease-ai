import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const chatApi = {
  // Which optional chat features the backend has switched on.
  options: () =>
    client.get(ENDPOINTS.chat.options).then((r) => r.data),
  listSessions: () =>
    client.get(ENDPOINTS.chat.sessions).then((r) => r.data),
  history: (sessionId) =>
    client.get(ENDPOINTS.chat.history(sessionId)).then((r) => r.data),
  /**
   * Ask the AI legal assistant. Returns the spec response shape:
   *   { response: string, sources: string[], session_id: string }
   * `payload` shape: { message, session_id?, case_id?, family? ("auto" | "off") }
   */
  sendMessage: (payload) =>
    client.post(ENDPOINTS.chat.message, payload).then((r) => r.data),
  // Backward-compat name used by older code
  ask: (payload) =>
    client.post(ENDPOINTS.chat.message, payload).then((r) => r.data),
};
