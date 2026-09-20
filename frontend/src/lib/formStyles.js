// Shared underline-input styling for every form on the paper/ink system —
// introduced on Login, reused everywhere else so the focus/error treatment
// stays identical across pages.
export function cnInput(hasError, extra = "") {
  const base =
    "w-full h-9 bg-transparent border-0 border-b text-sm text-ink-text placeholder:text-ink-muted/60 focus:outline-none transition-colors px-1 -mx-1";
  const border = hasError
    ? "border-brick bg-brick/[0.04]"
    : "border-hairline focus:border-ink-text focus:bg-ink-text/[0.03]";
  return `${base} ${border} ${extra}`;
}
