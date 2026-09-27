// Human-readable file size: 19650 -> "19.2 KB".
export function formatBytes(bytes) {
  const n = Number(bytes);
  if (!Number.isFinite(n)) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

// "other" -> "Other", "in_progress" -> "In progress".
export const humanize = (value) => {
  const s = String(value ?? "").replace(/_/g, " ").trim();
  return s ? s[0].toUpperCase() + s.slice(1) : s;
};
