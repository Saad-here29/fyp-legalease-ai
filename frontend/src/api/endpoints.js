/**
 * Centralized API endpoint constants — keeps URLs in one place
 * so renames or version bumps stay easy.
 */

export const ENDPOINTS = {
  auth: {
    login: "/auth/login",
    signup: "/auth/signup",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
    me: "/auth/me",
    forgotPassword: "/auth/forgot-password",
    verifyOtp: "/auth/verify-otp",
    resendOtp: "/auth/resend-otp",
  },
  users: {
    list: "/users",
    byId: (id) => `/users/${id}`,
    profile: "/users/profile",
  },
  cases: {
    list: "/cases",
    create: "/cases",
    stats: "/cases/stats",
    byId: (id) => `/cases/${id}`,
    timeline: (id) => `/cases/${id}/timeline`,
    assignClient: (id) => `/cases/${id}/assign-client`,
    updateStatus: (id) => `/cases/${id}/status`,
    documents: (id) => `/cases/${id}/documents`,
    saveResearch: (id) => `/cases/${id}/research`,
    hearings: (id) => `/cases/${id}/hearings`,
  },
  documents: {
    upload: "/documents/upload",
    byId: (id) => `/documents/${id}`,
    analyze: (id) => `/documents/${id}/analyze`,
    download: (id) => `/documents/${id}/download`,
  },
  chat: {
    sessions: "/chat/sessions",
    sessionById: (id) => `/chat/sessions/${id}`,
    message: "/chat/message",
    ask: "/chat/ask",
    history: (sessionId) => `/chat/sessions/${sessionId}/history`,
  },
  research: {
    search: "/research/search",
    stats: "/research/stats",
    byId: (id) => `/research/${id}`,
    similarCases: (id) => `/research/${id}/similar`,
  },
  ocr: {
    upload: "/ocr/upload",
    status: (jobId) => `/ocr/jobs/${jobId}`,
  },
  contracts: {
    list: "/contracts",
    draft: "/contracts/draft",
    byId: (id) => `/contracts/${id}`,
    versions: (id) => `/contracts/${id}/versions`,
    checkCompliance: (id) => `/contracts/${id}/check-compliance`,
  },
  simulator: {
    scenarios: "/simulator/scenarios",
    attempts: "/simulator/attempts",
    progress: (studentId) => `/students/${studentId}/progress`,
  },
  notifications: {
    list: "/notifications",
    markRead: (id) => `/notifications/${id}/read`,
  },
};
