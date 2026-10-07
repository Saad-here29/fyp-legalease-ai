import { ROUTES } from "@/constants";

// Wording and links for knowledge-base records, shared by the Knowledge Base
// page, Research results and AI Chat sources.

// "LegalEase corpus (Pakistan Code-derived)" / "user-supplied PDF - source URL
// to be confirmed" — never "official text".
export function sourceLabel(source) {
  if (!source) return "";
  if (source.startsWith("LegalEase corpus")) return "LegalEase corpus (Pakistan Code-derived)";
  if (source === "user-supplied PDF") return "user-supplied PDF - source URL to be confirmed";
  return source;
}

// "s.17 Matters to be considered …", "Schedule item 4 Restitution …"
export function sectionLabel(section, heading) {
  if (!section && !heading) return "";
  const num = section ? (/^\d/.test(section) ? `s.${section}` : section) : "";
  return [num, heading].filter(Boolean).join(" ");
}

// A judgment id ("judgment/<dataset>/<hash>") -> its page, scrolled to a paragraph if given.
export function judgmentPath(docId, para) {
  const [, source, hash] = (docId || "").split("/");
  if (!source || !hash) return null;
  const path = ROUTES.KNOWLEDGE_BASE_JUDGMENT.replace(":source", encodeURIComponent(source)).replace(":hash", encodeURIComponent(hash));
  return para != null ? `${path}?para=${para}` : path;
}

// A record id ("legalease-corpus/guardians-and-wards-act-1890/s17") -> its law's page with the record open.
export function kbRecordPath(recordId) {
  const parts = (recordId || "").split("/");
  if (parts.length < 3) return null;
  return `${ROUTES.KNOWLEDGE_BASE_LAW.replace(":id", encodeURIComponent(parts[1]))}?record=${encodeURIComponent(recordId)}`;
}

// "7 Oct 2026" from an ISO date (scraped fetch dates, kb-v2 C3).
export function shortDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
