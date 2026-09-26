// Design system v1 wordmark: arch mark + "LegalEase" in Newsreader + a small
// "AI" tag (docs/design_reference, pages 2 and 7). `onInk` flips the colours
// for the ink sidebar / hero panels.

export function ArchMark({ className = "h-7 w-7" }) {
  return (
    <svg viewBox="0 0 28 32" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M3 31V15C3 8 8 3.5 14 1.5C20 3.5 25 8 25 15V31" />
      <path d="M9 31V17C9 12.5 11 9.5 14 8C17 9.5 19 12.5 19 17V31" />
    </svg>
  );
}

export default function Wordmark({ onInk = false, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${onInk ? "text-ds-paper" : "text-ds-ink"} ${className}`}>
      <ArchMark />
      <span className="font-ds-serif font-medium text-[24px] leading-none tracking-tight">LegalEase</span>
      <span
        className={`font-ds-sans font-semibold text-[12px] leading-none tracking-[0.08em] px-1.5 py-1 rounded-ds-sm ${
          onInk ? "bg-ds-paper/85 text-ds-ink" : "bg-ds-ink text-ds-paper"
        }`}
      >
        AI
      </span>
    </span>
  );
}
