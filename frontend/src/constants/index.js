export const APP_NAME = import.meta.env.VITE_APP_NAME || "LegalEase AI";
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || "0.1.0";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const API_TIMEOUT_MS = Number(
  import.meta.env.VITE_API_TIMEOUT_MS || 30_000
);

export const ROLES = Object.freeze({
  LAWYER: "LAWYER",
  CLIENT: "CLIENT",
  STUDENT: "STUDENT",
});

export const CASE_STATUS = Object.freeze({
  CREATED: "CREATED",
  ASSIGNED: "ASSIGNED",
  IN_PROGRESS: "IN_PROGRESS",
  HEARING_SCHEDULED: "HEARING_SCHEDULED",
  CLOSED: "CLOSED",
});

export const CASE_TYPES = Object.freeze({
  DIVORCE: "DIVORCE",
  CUSTODY: "CUSTODY",
  INHERITANCE: "INHERITANCE",
  MAINTENANCE: "MAINTENANCE",
});

export const STORAGE_KEYS = Object.freeze({
  ACCESS_TOKEN: "legalease.access_token",
  REFRESH_TOKEN: "legalease.refresh_token",
  USER: "legalease.user",
});

export const ROUTES = Object.freeze({
  LANDING: "/",
  LOGIN: "/login",
  SIGNUP: "/signup",
  WELCOME: "/welcome",
  FORGOT_PASSWORD: "/forgot-password",
  RESET_PASSWORD: "/reset-password",
  OTP: "/verify-otp",

  // Role dashboards
  LAWYER_DASHBOARD: "/lawyer/dashboard",
  CLIENT_DASHBOARD: "/client/dashboard",
  STUDENT_DASHBOARD: "/student/dashboard",

  // Feature areas (resolved per-role)
  CASES: "/cases",
  CASE_DETAIL: "/cases/:id",
  CHATBOT: "/chatbot",
  RESEARCH: "/research",
  RESEARCH_DETAIL: "/research/:id",
  DOCUMENTS: "/documents",
  CONTRACTS: "/contracts",
  SIMULATOR: "/simulator",
  NOTIFICATIONS: "/notifications",
  PROFILE: "/profile",
});
