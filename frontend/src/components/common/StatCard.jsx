/**
 * Stat highlight for the landing page Stats section — flat, hairline-divided
 * column (no rounded card, no shadow, no gold).
 */
export default function StatCard({ value, label, helper, last = false }) {
  return (
    <div className={`px-6 first:pl-0 ${last ? "" : "sm:border-r border-hairline"}`}>
      <div className="text-4xl lg:text-5xl font-editorial text-ink-text leading-none">
        {value}
      </div>
      <div className="mt-3 text-sm font-medium text-ink-text">{label}</div>
      {helper && <p className="mt-1 text-sm text-ink-muted">{helper}</p>}
    </div>
  );
}
