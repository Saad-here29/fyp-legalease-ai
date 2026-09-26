import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { citeAnchor } from "./citations";

// The one renderer for AI-generated content — chat answers, document
// summaries, drafted contracts — styled by `prose prose-ink` (Tailwind
// typography, theme in tailwind.config.js).
//
// Safety: react-markdown never renders raw HTML from the model's output.
// The only tag let through is <br> — the model writes it inside table cells
// — which `rehypeBreaks` turns into a real line break; any other raw HTML
// is dropped.
//
// Citations: "[3]" in an answer refers to retrieved passage 3. Pass
// `citeId` (unique per message) and each marker becomes a superscript link
// to the footnote with id `cite-<citeId>-3` (see ./citations.js).

const BR = /^<br\s*\/?>$/i;

function rehypeBreaks() {
  const walk = (node) => {
    if (!node.children) return;
    node.children = node.children.flatMap((child) => {
      if (child.type === "raw") {
        return BR.test(child.value.trim())
          ? [{ type: "element", tagName: "br", properties: {}, children: [] }]
          : [];
      }
      walk(child);
      return [child];
    });
  };
  return walk;
}

// "[3]" -> a link react-markdown can render; `a` below turns it into a
// footnote marker. Skips real markdown links ("[text](url)").
function linkCitations(text, citeId) {
  return text.replace(/\[(\d{1,2})\](?!\()/g, (_, n) => `[${n}](#${citeAnchor(citeId, n)})`);
}

// eslint-disable-next-line no-unused-vars -- `node` is react-markdown's AST prop; keep it off the DOM
const citationLink = ({ node, href, children, ...props }) =>
  href?.startsWith("#cite-") ? (
    <sup className="citation-marker">
      <a href={href} className="no-underline">
        {children}
      </a>
    </sup>
  ) : (
    <a href={href} target="_blank" rel="noreferrer" {...props}>
      {children}
    </a>
  );

export default function Markdown({ children, citeId, className = "" }) {
  const text = children || "";
  return (
    <div className={`prose prose-ink max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeBreaks]}
        components={{ a: citationLink }}
      >
        {citeId ? linkCitations(text, citeId) : text}
      </ReactMarkdown>
    </div>
  );
}
