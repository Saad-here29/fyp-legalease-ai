// Minimal inline renderer for AI chat answers: **bold**, [n] citation
// markers (superscript footnotes, per the design system) and line breaks.
// Escapes HTML first so the AI's own output can't inject markup. For text
// with headings, lists, rules or tables (document summaries, drafted
// contracts) use the MarkdownBlocks component instead.
export function renderInline(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\[(\d+)\]/g, '<sup class="citation-marker">$1</sup>')
    .replace(/\n/g, "<br/>");
}
