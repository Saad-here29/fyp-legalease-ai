// Footnote anchor ids for "[n]" citation markers — unique per message, so
// two answers on one page can both have a footnote 1.
export const citeAnchor = (citeId, n) => `cite-${citeId}-${n}`;
