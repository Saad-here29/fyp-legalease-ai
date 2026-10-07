import { Link } from "react-router-dom";
import { ROUTES } from "@/constants";

// Shared pieces of the three dashboards — design system v1 (docs/architecture/design_reference
// pages 4-6): a figure row opened by a 2px ink rule, ruled sections with an
// optional "View all" link, and the recent-AI-conversations list.

export function Figures({ items }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 border-t-2 border-ds-ink border-b border-b-ds-rule">
      {items.map(({ label, value, helper }, i) => (
        <div
          key={label}
          className={`py-6 pr-6 ${i % 2 ? "pl-6" : ""} ${i > 1 ? "border-t border-ds-rule lg:border-t-0" : ""} ${
            i > 0 ? "lg:pl-6 lg:border-l lg:border-ds-rule" : ""
          } ${i % 2 ? "border-l border-ds-rule" : ""}`}
        >
          <p className="ds-body text-ds-text-2">{label}</p>
          <p className="ds-figure mt-2">{value}</p>
          {helper && <p className="ds-body text-ds-text-2 mt-1">{helper}</p>}
        </div>
      ))}
    </div>
  );
}

export function RuledSection({ title, action, children, className = "" }) {
  return (
    <section className={className}>
      <div className="flex items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
        <h2 className="ds-h2">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function ViewAll({ to, children }) {
  return (
    <Link to={to} className="ds-link text-[15px] mb-1">
      {children}
    </Link>
  );
}

export function SessionList({ sessions, limit = 4 }) {
  if (!sessions || sessions.length === 0) {
    return <p className="ds-body text-ds-text-2 py-5">No AI conversations yet.</p>;
  }
  return (
    <ul>
      {sessions.slice(0, limit).map((s) => (
        <li key={s.id} className="border-b border-ds-rule">
          <Link
            to={ROUTES.CHATBOT}
            className="block py-4 hover:bg-ds-sheet/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-ink"
          >
            <span className="block font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text line-clamp-2" dir="auto">
              {s.title || "Untitled"}
            </span>
            <span className="ds-meta">
              {s.total_messages} message{s.total_messages === 1 ? "" : "s"} ·{" "}
              {new Date(s.updated_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function Today() {
  return new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}
