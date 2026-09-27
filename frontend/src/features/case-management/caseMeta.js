import { formatBytes, humanize } from "@/lib/format";

// Shared case labels for the Cases list and Case detail (design system v1).
// Statuses are the backend's CaseStatus values. No status is shown in Seal:
// Seal marks action that's due, and cases carry no hearing or due dates.

export const STATUS = {
  created: { label: "Created", tag: "ds-tag-neutral" },
  assigned: { label: "Assigned", tag: "ds-tag-neutral" },
  in_progress: { label: "In progress", tag: "ds-tag-active" },
  hearing_scheduled: { label: "Hearing scheduled", tag: "ds-tag-active" },
  closed: { label: "Closed", tag: "ds-tag bg-ds-disabled text-ds-text-2" },
};

export const TYPE_LABEL = {
  divorce: "Divorce",
  custody: "Custody",
  inheritance: "Inheritance",
  maintenance: "Maintenance",
};

export const fmtDate = (value) =>
  value ? new Date(value).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";

// The timeline API (backend CaseService.timeline) builds its text from raw
// enum values: "Status: assigned → in_progress", "Filed as custody at …",
// "other · 19650 bytes". Reword those for display; anything else passes
// through unchanged.
const statusLabel = (v) => STATUS[v]?.label || humanize(v);

export function readableTimelineEntry(entry) {
  const e = { ...entry };
  const status = /^Status:\s*(\w+)\s*→\s*(\w+)\s*$/.exec(e.title || "");
  if (status) {
    e.title = `Status changed to ${statusLabel(status[2])}`;
    e.description = `from ${statusLabel(status[1])}`;
  }
  if (e.kind === "CREATED" && e.description) {
    e.description = e.description.replace(/^Filed as (\w+)/, (_, t) => `Filed as ${TYPE_LABEL[t] || humanize(t)}`);
  }
  if (e.kind === "DOCUMENT" && e.description) {
    e.description = e.description
      .replace(/^([a-z_]+)(?= ·)/, (t) => humanize(t))
      .replace(/(\d+) bytes/, (_, n) => formatBytes(n));
  }
  return e;
}
