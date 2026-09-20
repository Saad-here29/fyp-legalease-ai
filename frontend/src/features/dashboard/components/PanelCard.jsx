// Flat panel: serif title, muted description, hairline divider, content.
// Replaces the old rounded/shadowed/backdrop-blur PanelCard — same import
// path is kept so every page that already imports PanelCard picks up the
// new look with no import changes needed.
export default function PanelCard({ title, description, action, children, className = "" }) {
  return (
    <section className={className}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 mb-1">
          {title && <h2 className="font-editorial text-xl text-ink-text">{title}</h2>}
          {action}
        </div>
      )}
      {description && <p className="text-sm text-ink-muted mb-2">{description}</p>}
      <div className="border-t border-hairline pt-1 mt-3">{children}</div>
    </section>
  );
}
