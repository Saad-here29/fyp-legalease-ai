import client from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";

export const authApi = {
  login: (data) => client.post(ENDPOINTS.auth.login, data).then((r) => r.data),
  signup: (data) => client.post(ENDPOINTS.auth.signup, data).then((r) => r.data),
  // Same payload as signup; the server treats /register and /signup as aliases.
  register: (data) => client.post(ENDPOINTS.auth.signup, data).then((r) => r.data),
  refresh: () => client.post(ENDPOINTS.auth.refresh, {}).then((r) => r.data),
  me: () => client.get(ENDPOINTS.auth.me).then((r) => r.data),
  logout: () => client.post(ENDPOINTS.auth.logout).then((r) => r.data),
  forgotPassword: (email) =>
    client.post(ENDPOINTS.auth.forgotPassword, { email }).then((r) => r.data),
  resetPassword: ({ email, otp, new_password }) =>
    client
      .post("/auth/reset-password", { email, otp, new_password })
      .then((r) => r.data),
  verifyOtp: ({ email, otp }) =>
    client.post(ENDPOINTS.auth.verifyOtp, { email, otp }).then((r) => r.data),
  resendOtp: (email) =>
    client.post(ENDPOINTS.auth.resendOtp, { email }).then((r) => r.data),
};

export function dashboardRouteFor(role) {
  switch (role) {
    case "lawyer":
      return "/lawyer/dashboard";
    case "client":
      return "/client/dashboard";
    case "student":
      return "/student/dashboard";
    default:
      return "/";
  }
}

export function extractAuthError(err) {
  const data = err?.response?.data?.error;
  if (data?.message) {
    return { message: data.message, hint: data.hint };
  }
  return {
    message: "Something went wrong.",
    hint: "Please check your connection and try again.",
  };
}
