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
  },
  documents: {
    upload: "/documents/upload",
    capabilities: "/documents/capabilities",
    analyze: (id) => `/documents/${id}/analyze`,
  },
  chat: {
    sessions: "/chat/sessions",
    message: "/chat/message",
    options: "/chat/options",
    history: (sessionId) => `/chat/sessions/${sessionId}/history`,
  },
  research: {
    search: "/research/search",
    stats: "/research/stats",
  },
  kb: {
    stats: "/kb/stats",
    documents: "/kb/documents",
    document: (id) => `/kb/documents/${encodeURIComponent(id)}`,
    sections: (id) => `/kb/documents/${encodeURIComponent(id)}/sections`,
    download: (id) => `/kb/documents/${encodeURIComponent(id)}/download`,
    original: (id) => `/kb/documents/${encodeURIComponent(id)}/original`,
    // Record ids contain "/" ("legalease-corpus/<law>/s17"); each part is encoded.
    record: (recordId) => `/kb/records/${recordId.split("/").map(encodeURIComponent).join("/")}`,
    // Judgments (kb-v2 C2; 404 while JUDGMENTS_V2 is off)
    judgments: "/kb/judgments",
    judgment: (docId) => `/kb/judgments/${docId.split("/").map(encodeURIComponent).join("/")}`,
  },
  contracts: {
    list: "/contracts",
    draft: "/contracts/draft",
    byId: (id) => `/contracts/${id}`,
    versions: (id) => `/contracts/${id}/versions`,
    checkCompliance: (id) => `/contracts/${id}/check-compliance`,
  },
};
