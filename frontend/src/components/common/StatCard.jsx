/**
 * Stat highlight for the landing page Stats section — flat, hairline-divided
 * column (no rounded card, no shadow, no gold).
 */
export default function StatCard({ value, label, helper, last = false }) {
  return (
    <div className={`px-6 first:pl-0 ${last ? "" : "sm:border-r border-hairline"}`}>
      <div className="text-5xl lg:text-6xl font-editorial text-ink-text leading-none tracking-tight">
        {value}
      </div>
      <div className="mt-4 text-base font-semibold text-ink-text">{label}</div>
      {helper && <p className="mt-1 text-[15px] text-ink-muted">{helper}</p>}
    </div>
  );
}
