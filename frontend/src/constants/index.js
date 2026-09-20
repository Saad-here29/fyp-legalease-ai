export const APP_NAME = import.meta.env.VITE_APP_NAME || "LegalEase AI";
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || "0.1.0";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const API_TIMEOUT_MS = Number(
  import.meta.env.VITE_API_TIMEOUT_MS || 30_000
);

// Values are lowercase to match the backend's actual enum values
// (backend/app/models/enums.py). Keys stay uppercase since those are just
// the JS identifiers callers use (ROLES.LAWYER, CASE_STATUS.CREATED, ...).
export const ROLES = Object.freeze({
  LAWYER: "lawyer",
  CLIENT: "client",
  STUDENT: "student",
});

export const CASE_STATUS = Object.freeze({
  CREATED: "created",
  ASSIGNED: "assigned",
  IN_PROGRESS: "in_progress",
  HEARING_SCHEDULED: "hearing_scheduled",
  CLOSED: "closed",
});

export const CASE_TYPES = Object.freeze({
  DIVORCE: "divorce",
  CUSTODY: "custody",
  INHERITANCE: "inheritance",
  MAINTENANCE: "maintenance",
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
