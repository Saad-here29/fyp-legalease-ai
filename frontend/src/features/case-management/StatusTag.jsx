import { STATUS } from "./caseMeta";

// Case status as a design-system tag (labels and styles in ./caseMeta.js).
export default function StatusTag({ status, className = "" }) {
  const s = STATUS[status] || { label: status, tag: "ds-tag-neutral" };
  return <span className={`${s.tag} h-7 whitespace-nowrap ${className}`}>{s.label}</span>;
}
