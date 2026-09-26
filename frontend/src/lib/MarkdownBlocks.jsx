// Renders the block-level markdown the LLM writes in document summaries and
// drafted contracts: "**1) Summary**" / "### 1. Definitions" headings,
// "---" rules, bullet and numbered lists (numbering kept — contract clauses
// are numbered) and pipe tables (often with <br> inside cells).
// Text is HTML-escaped before any markup is added, so the model's output
// can't inject tags. For chat answers with [n] citation markers, use
// renderInline from ./markdownLite instead.

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s) {
  return escapeHtml(s)
    .replace(/&lt;br\s*\/?&gt;/gi, "<br/>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^\w*])\*(?!\s)([^*]+?)\*(?!\w)/g, "$1<em>$2</em>");
}

const TABLE_SEP = /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$/;
const BULLET = /^[-*+•]\s+(.*)$/;
const NUMBERED = /^(\d{1,3})[.)]\s+(.*)$/;
const HEADING = /^(?:#{1,6}\s+(.+)|\*\*([^*].*?)\*\*:?)$/;

function cells(line) {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
}

function toBlocks(text) {
  const blocks = [];
  const lines = (text || "").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    // "___" is deliberately not a rule: in contracts it's a signature line.
    if (/^(-{3,}|\*{3,})$/.test(line)) {
      blocks.push({ type: "rule" });
    } else if (line.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const l = lines[i].trim();
        if (!TABLE_SEP.test(l)) rows.push(cells(l));
        i++;
      }
      i--;
      blocks.push({ type: "table", head: rows[0] || [], rows: rows.slice(1) });
    } else if (HEADING.test(line)) {
      const m = line.match(HEADING);
      blocks.push({ type: "heading", text: m[1] || m[2] });
    } else if (BULLET.test(line) || NUMBERED.test(line)) {
      const num = line.match(NUMBERED);
      const ordered = !!num;
      const item = ordered ? num[2] : line.match(BULLET)[1];
      const last = blocks[blocks.length - 1];
      if (last?.type === "list" && last.ordered === ordered) last.items.push(item);
      else blocks.push({ type: "list", ordered, start: ordered ? Number(num[1]) : 1, items: [item] });
    } else {
      blocks.push({ type: "para", text: line });
    }
  }
  return blocks;
}

export default function MarkdownBlocks({ text }) {
  const html = (s) => ({ __html: inline(s) });
  return (
    <div className="space-y-3 text-sm text-ink-text leading-relaxed [&_strong]:font-medium">
      {toBlocks(text).map((b, i) => {
        if (b.type === "rule") return <hr key={i} className="border-hairline-subtle" />;
        if (b.type === "heading")
          return <h3 key={i} className="font-medium pt-2" dangerouslySetInnerHTML={html(b.text)} />;
        if (b.type === "list") {
          const List = b.ordered ? "ol" : "ul";
          return (
            <List
              key={i}
              start={b.ordered ? b.start : undefined}
              className={`${b.ordered ? "list-decimal" : "list-disc"} pl-5 space-y-1`}
            >
              {b.items.map((it, j) => (
                <li key={j} dangerouslySetInnerHTML={html(it)} />
              ))}
            </List>
          );
        }
        if (b.type === "table")
          return (
            <div key={i} className="overflow-x-auto">
              <table className="w-full text-left text-sm border-t border-hairline">
                <thead>
                  <tr className="border-b border-hairline">
                    {b.head.map((c, j) => (
                      <th key={j} className="py-2 pr-4 font-medium text-ink-muted align-top" dangerouslySetInnerHTML={html(c)} />
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {b.rows.map((r, j) => (
                    <tr key={j} className="border-b border-hairline-subtle">
                      {r.map((c, k) => (
                        <td key={k} className="py-2 pr-4 align-top" dangerouslySetInnerHTML={html(c)} />
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        return <p key={i} dangerouslySetInnerHTML={html(b.text)} />;
      })}
    </div>
  );
}
