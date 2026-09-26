// Footnote anchor ids for "[n]" citation markers — unique per message, so
// two answers on one page can both have a footnote 1.
export const citeAnchor = (citeId, n) => `cite-${citeId}-${n}`;

// The model sometimes cites in its own format — "【5】", "【5†L1-L3】",
// "【4, 5】". The backend rewrites these to "[n]" before its citation check
// (backend/app/ai/citation_check.py: normalize_markers); answers stored
// before that fix are rewritten here, the same way, when displayed.
const FULLWIDTH_MARKER = /【\s*(\d{1,2}(?:\s*,\s*\d{1,2})*)\s*(?:†[^】]*)?】/g;

export const normalizeMarkers = (text) =>
  (text || "").replace(FULLWIDTH_MARKER, (_, nums) =>
    nums.split(",").map((n) => `[${n.trim()}]`).join("")
  );
