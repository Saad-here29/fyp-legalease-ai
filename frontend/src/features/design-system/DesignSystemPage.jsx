import { Check, X, AlertTriangle } from "lucide-react";

// Test page for design system v1 tokens (docs/design_reference, page 1).
// Not linked from the app; open /design-system to check the tokens render
// as specified before any real page migrates to them.

const COLOURS = [
  ["ink", "#0F2A22", "Identity panels, sidebar, section rules"],
  ["ink-2", "#173A2F", "Raised areas on ink, active pill"],
  ["paper", "#F4EFE4", "Page background"],
  ["sheet", "#FBF8F2", "Documents, ledgers, inputs"],
  ["rule", "#D9D0BD", "Hairlines, borders"],
  ["text", "#14201A", "Headings and body · 14.6:1 on Paper"],
  ["text-2", "#45504A", "Secondary, labels · 7.3:1"],
  ["seal", "#9E2B1D", "The accent: act here · 6.5:1, white on it 7.5:1"],
  ["pass", "#17553A", "Checks that pass, verified · 7.6:1"],
  ["review", "#8A5300", "Needs a human look · 5.5:1"],
];

const SWATCH = {
  ink: "bg-ds-ink", "ink-2": "bg-ds-ink-2", paper: "bg-ds-paper", sheet: "bg-ds-sheet", rule: "bg-ds-rule",
  text: "bg-ds-text", "text-2": "bg-ds-text-2", seal: "bg-ds-seal", pass: "bg-ds-pass", review: "bg-ds-review",
};

const TYPE = [
  ["ds-display", "Display", "Newsreader 500 · 72/76", "Cited to the section."],
  ["ds-h1", "H1 · page title", "Newsreader 500 · 48/56", "Malik Enterprises v. Horizon Developers"],
  ["ds-h2", "H2 · section", "Newsreader 500 · 32/40", "Cause list this week"],
  ["ds-h3", "H3 · block", "Plex Sans 600 · 24/32", "When the limitation clock starts"],
  ["ds-h4", "H4 · group", "Plex Sans 600 · 19/28", "Parties to the agreement"],
  ["ds-body", "Body", "Plex Sans 400 · 16/26 · min.",
    "A suit for specific performance must be filed within three years from the date fixed for performance or, if no date is fixed, from when the plaintiff has notice that performance is refused."],
  ["ds-meta", "Label · meta", "Plex Sans 500 · 14/20", "Metadata, table headers and captions only — never reading text."],
];

const SPACE = [["1", 4], ["2", 8], ["3", 12], ["4", 16], ["6", 24], ["8", 32], ["12", 48], ["16", 64], ["24", 96]];

function Section({ number, title, note, children }) {
  return (
    <section className="ds-section grid gap-8 lg:grid-cols-[260px_1fr] pb-12">
      <div>
        <p className="font-ds-serif text-[20px] text-ds-text-2">§ {number}</p>
        <h2 className="ds-h2">{title}</h2>
        {note && <p className="ds-body text-ds-text-2 mt-3">{note}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-ds-paper font-ds-sans text-ds-text">
      <header className="bg-ds-ink text-ds-paper">
        <div className="max-w-ds-content mx-auto px-6 lg:px-14 py-12">
          <p className="ds-eyebrow text-ds-paper/70">LegalEase AI · Design system v1 · token test page</p>
          <h1 className="ds-display text-ds-paper mt-4">A docket, not a dashboard.</h1>
        </div>
      </header>

      <main className="max-w-ds-content mx-auto px-6 lg:px-14 pt-12 space-y-12">
        <Section number="01" title="Colour" note="Ink and paper carry the page. Seal is the one accent, and it only ever means act here.">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {COLOURS.map(([name, hex, use]) => (
              <div key={name}>
                <div className={`h-16 rounded-ds border border-ds-rule ${SWATCH[name]}`} />
                <p className="ds-h4 mt-2 text-[16px] leading-[22px]">{name}</p>
                <p className="ds-meta">{hex}</p>
                <p className="ds-meta mt-1">{use}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-6 sm:grid-cols-3 mt-8 pt-6 border-t border-ds-rule ds-body">
            <p><strong>Seal is used for:</strong> primary buttons, the active tab or nav item, numbers that need action, failing checks.</p>
            <p><strong>Seal is never used for:</strong> headings, decoration, backgrounds larger than a button, or more than one primary button per view.</p>
            <p><strong>Contrast (measured):</strong> text 14.6:1 on Paper; text-2 7.3:1; seal 6.5:1 on Paper and 7.5:1 under white text.</p>
          </div>
        </Section>

        <Section number="02" title="Type" note="Newsreader for identity and page titles. IBM Plex Sans for everything you work in. Body never drops below 16px.">
          {TYPE.map(([cls, label, spec, sample]) => (
            <div key={cls} className="grid gap-4 sm:grid-cols-[200px_1fr] py-5 border-b border-ds-rule">
              <div>
                <p className="font-ds-sans font-semibold text-[14px]">{label}</p>
                <p className="ds-meta">{spec}</p>
                <code className="ds-meta text-ds-text-2/80">.{cls}</code>
              </div>
              <p className={cls}>{sample}</p>
            </div>
          ))}
          <div className="grid gap-4 sm:grid-cols-[200px_1fr] py-5 items-center">
            <div>
              <p className="font-ds-sans font-semibold text-[14px]">Figure</p>
              <p className="ds-meta">Plex Sans 500 · 44/48 · tabular</p>
            </div>
            <div className="flex items-baseline gap-10">
              <span className="ds-figure text-ds-seal">04</span>
              <span className="ds-figure">23</span>
              <span className="ds-meta">Seal only when the number asks for action.</span>
            </div>
          </div>
        </Section>

        <Section number="03" title="Space & structure" note="An 8px base. Sections are ruled: a 2px ink line opens a section, 1px hairlines divide rows. Corners 2–4px. No drop shadows.">
          <div className="flex items-end gap-4">
            {SPACE.map(([cls, px]) => (
              <div key={px} className="text-center">
                <div className="bg-ds-ink mx-auto" style={{ width: px, height: px }} />
                <p className="ds-meta mt-2">{px}</p>
                <p className="ds-meta text-ds-text-2/70">{cls}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-6 sm:grid-cols-3 mt-8 ds-body">
            <p><strong>Page gutter</strong> 56px in the app (<code>px-14</code>), 96px on marketing (<code>px-24</code>). Content column max 1064px (<code>max-w-ds-content</code>).</p>
            <p><strong>Rhythm</strong> 48px between sections, 24px inside, 16px between label and control.</p>
            <p><strong>Rows</strong> 64–72px tall (<code>.ds-row</code>), never less than 44px touch height for anything clickable.</p>
          </div>
        </Section>

        <Section number="04" title="Components" note="The same parts on every screen. One primary button per view.">
          <p className="ds-eyebrow mb-3">Buttons</p>
          <div className="flex flex-wrap items-center gap-4">
            <button className="ds-btn-primary">Ask about this case</button>
            <button className="ds-btn-secondary">Add document</button>
            <a href="#components" className="ds-link">View all hearings</a>
            <button className="ds-btn-disabled" disabled>Disabled</button>
          </div>

          <p className="ds-eyebrow mt-8 mb-3">Status</p>
          <div className="flex flex-wrap items-center gap-3">
            <span className="ds-tag-pass"><Check className="h-4 w-4" strokeWidth={2.5} />Passes</span>
            <span className="ds-tag-fail"><X className="h-4 w-4" strokeWidth={2.5} />Fails</span>
            <span className="ds-tag-review"><AlertTriangle className="h-4 w-4" strokeWidth={2.5} />Review</span>
            <span className="ds-tag-neutral">Adjourned</span>
            <span className="ds-tag-active">Active</span>
          </div>

          <p className="ds-eyebrow mt-8 mb-3">Input <span className="normal-case tracking-normal font-normal">(derived from the Login / Search mockups)</span></p>
          <div className="max-w-md">
            <label className="ds-label" htmlFor="ds-email">Email</label>
            <input id="ds-email" className="ds-input" placeholder="ayesha.khan@chambers.pk" />
          </div>

          <p className="ds-eyebrow mt-8 mb-3">Ruled list <span className="normal-case tracking-normal font-normal">(derived from the Cases / Deadlines mockups)</span></p>
          <div className="border-t-2 border-ds-ink">
            {[["Muslim Family Laws Ordinance, 1961 — Section 6", "Polygamy", "ds-tag-pass", "Verified"],
              ["Muslim Family Laws Ordinance, 1961 — Section 7", "Talaq", "ds-tag-review", "Review"]].map(([t, s, tag, label]) => (
              <div key={t} className="ds-row flex items-center justify-between gap-4">
                <div>
                  <p className="font-ds-sans font-semibold text-[17px]">{t}</p>
                  <p className="ds-meta">{s}</p>
                </div>
                <span className={tag}>{label}</span>
              </div>
            ))}
          </div>
        </Section>
      </main>
    </div>
  );
}
