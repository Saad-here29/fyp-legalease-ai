export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const API_TIMEOUT_MS = Number(
  import.meta.env.VITE_API_TIMEOUT_MS || 30_000
);

// Values are lowercase to match the backend's actual enum values
// (backend/app/models/enums.py). Keys stay uppercase since those are just
// the JS identifiers callers use (ROLES.LAWYER, ...).
export const ROLES = Object.freeze({
  LAWYER: "lawyer",
  CLIENT: "client",
  STUDENT: "student",
});


// Matches backend/app/models/enums.py CaseType.
export const CASE_TYPES = Object.freeze({
  CIVIL: "civil",
  CRIMINAL: "criminal",
  COMMERCIAL: "commercial",
  PROPERTY: "property",
  SERVICE: "service",
  DIVORCE: "divorce",
  CUSTODY: "custody",
  INHERITANCE: "inheritance",
  MAINTENANCE: "maintenance",
});

// Matches backend/app/models/enums.py ContractType exactly.
export const CONTRACT_TYPES = Object.freeze({
  NDA: "nda",
  EMPLOYMENT: "employment",
  SERVICE_AGREEMENT: "service_agreement",
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
  KNOWLEDGE_BASE: "/knowledge-base",
  KNOWLEDGE_BASE_LAW: "/knowledge-base/:id",
  KNOWLEDGE_BASE_JUDGMENT: "/knowledge-base/judgments/:source/:hash",
  DOCUMENTS: "/documents",
  CONTRACTS: "/contracts",
  CONTRACT_DETAIL: "/contracts/:id",
});

// The dashboard a signed-in user belongs on (login, wrong-role redirects,
// the 404 page). One map instead of three copies.
const DASHBOARD_BY_ROLE = Object.freeze({
  [ROLES.LAWYER]: ROUTES.LAWYER_DASHBOARD,
  [ROLES.CLIENT]: ROUTES.CLIENT_DASHBOARD,
  [ROLES.STUDENT]: ROUTES.STUDENT_DASHBOARD,
});

export const dashboardRouteFor = (role) => DASHBOARD_BY_ROLE[role] || ROUTES.LANDING;
