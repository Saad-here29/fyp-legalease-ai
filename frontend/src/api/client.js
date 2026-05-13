import axios from "axios";
import { API_BASE_URL, API_TIMEOUT_MS } from "@/constants";

/**
 * Axios instance — sends HttpOnly auth cookies with every request via
 * `withCredentials`. The backend reads `le_access` / `le_refresh` cookies;
 * we never touch tokens in JavaScript.
 */
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// On 401: try to refresh once, then retry the original request. If the
// refresh itself 401s, the cookies are dead — clear local state and bounce
// to /login.
let isRefreshing = false;
let pendingQueue = [];

const flushQueue = (error) => {
  pendingQueue.forEach((p) => (error ? p.reject(error) : p.resolve()));
  pendingQueue = [];
};

const REFRESHABLE_PATHS_DENY = ["/auth/login", "/auth/refresh", "/auth/register", "/auth/signup", "/auth/verify-email", "/auth/verify-otp"];

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const url = original?.url || "";
    const isRefreshable =
      error.response?.status === 401 &&
      !original?._retry &&
      !REFRESHABLE_PATHS_DENY.some((p) => url.endsWith(p));

    if (!isRefreshable) return Promise.reject(error);

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      })
        .then(() => client(original))
        .catch((e) => Promise.reject(e));
    }

    original._retry = true;
    isRefreshing = true;

    try {
      await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true, timeout: API_TIMEOUT_MS }
      );
      flushQueue(null);
      return client(original);
    } catch (refreshErr) {
      flushQueue(refreshErr);
      // Dynamic import avoids a hard frontend-→-store circular dep
      try {
        const { useAuthStore } = await import("@/store/authStore");
        useAuthStore.getState().clear();
      } catch {
        // ignore
      }
      // Hard bounce to login — query-string preserves where we were
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }
);

export default client;
