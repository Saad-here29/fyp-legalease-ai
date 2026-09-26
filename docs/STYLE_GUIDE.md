# Style Guide — Design system v1 (2026)

> Referenced by `PROJECT_CONTEXT.md`: "Follow the style rules in
> STYLE_GUIDE.md exactly — do not improvise colors, fonts, or spacing."
>
> **Source of truth:** `docs/design_reference/LegalEase AI Design System.pdf`
> (13 pages; rendered as `page-01.jpg` … `page-13.jpg` in the same folder).
> Page 1 defines the rules below; pages 2–13 are screen mockups.
>
> **Replaces** the previous editorial system (Georgia + Inter, "brick"
> accent restricted to links and citation markers). Those rules no longer
> apply. See "Migration status" at the bottom for which pages have moved.

*"A docket, not a dashboard." Two typefaces, one accent, ruled sections
instead of floating cards — and AI output that always shows where it came
from.*

## §01 Colour

Ink and paper carry the page. **Seal** — the red of wax seals and red tape —
is the one accent, and it only ever means *act here*.

| Token (Tailwind) | Hex | Use |
|---|---|---|
| `ds-ink` | `#0F2A22` | Identity panels, sidebar, section rules |
| `ds-ink-2` | `#173A2F` | Raised areas on ink, active pill |
| `ds-paper` | `#F4EFE4` | Page background |
| `ds-sheet` | `#FBF8F2` | Documents, ledgers, inputs |
| `ds-rule` | `#D9D0BD` | Hairlines, borders |
| `ds-text` | `#14201A` | Headings and body |
| `ds-text-2` | `#45504A` | Secondary, labels |
| `ds-seal` | `#9E2B1D` | The accent: act here |
| `ds-pass` | `#17553A` | Checks that pass, verified |
| `ds-review` | `#8A5300` | Needs a human look |

Supporting values sampled from the page-1 component row: `ds-pass-tint`
`#DEEBE1`, `ds-seal-tint` `#F4E1DA`, `ds-review-tint` `#F6E8CD`, `ds-disabled`
`#E6DFCF`, `ds-underline` `#C7BBA5` (text-link underline).

**Seal is used for:** primary buttons, the active tab or nav item, numbers
that need action (hearings this week, due dates), failing checks.

**Seal is never used for:** headings, decoration, backgrounds larger than a
button, or more than one primary button per view.

**Contrast.** Page 1 states body text 14.8:1 on Paper, secondary 7.6:1, Seal
7.1:1 on Paper and 7.6:1 under white text. Measured from the hex values (WCAG
2.x formula): text **14.6:1**, text-2 **7.3:1**, seal **6.5:1** on Paper and
**7.5:1** under white, pass 7.6:1, review 5.5:1. All meet WCAG AA for body
text (4.5:1); text, text-2 and pass also meet AAA (7:1).

## §02 Type

**Newsreader** for identity and page titles — the voice of the bench. **IBM
Plex Sans** for everything you work in. Body never drops below 16px; each
step up is at least ×1.25.

| Role | Class | Spec (weight · size/line-height) |
|---|---|---|
| Display | `.ds-display` | Newsreader 500 · 72/76 |
| H1 · page title | `.ds-h1` | Newsreader 500 · 48/56 |
| H2 · section | `.ds-h2` | Newsreader 500 · 32/40 |
| H3 · block | `.ds-h3` | Plex Sans 600 · 24/32 |
| H4 · group | `.ds-h4` | Plex Sans 600 · 19/28 |
| Body | `.ds-body` | Plex Sans 400 · 16/26 · minimum |
| Label · meta | `.ds-meta` | Plex Sans 500 · 14/20 — metadata, table headers and captions only, never reading text |
| Figure | `.ds-figure` | Plex Sans 500 · 44/48 · tabular — Seal only when the number asks for action |

Font families: `font-ds-serif` (Newsreader) and `font-ds-sans` (IBM Plex
Sans), loaded from Google Fonts in `frontend/index.html`.

*Implementation note:* below the `lg` breakpoint Display renders at 44/48
and H1 at 36/44 so they fit a phone; each step stays at least ×1.25 apart.

## §03 Space & structure

An 8px base. Sections are *ruled*: a **2px ink line opens a section**, **1px
hairlines divide rows**. Corners are 2–4px (`rounded-ds-sm` / `rounded-ds`).
**No drop shadows.**

| Rule | Value | Tailwind |
|---|---|---|
| Spacing scale | 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 | `1 · 2 · 3 · 4 · 6 · 8 · 12 · 16 · 24` (Tailwind's default scale already matches) |
| Page gutter | 56px in the app, 96px on marketing | `px-14`, `px-24` |
| Content column | max 1064px | `max-w-ds-content` |
| Rhythm | 48px between sections, 24px inside, 16px between label and control | `gap-12` / `gap-6` / `mb-4` |
| Rows | 64–72px tall; never less than 44px touch height for anything clickable | `.ds-row`, `min-h-[44px]` |

Structure classes: `.ds-section` (2px ink top rule + 24px padding) and
`.ds-row` (1px rule bottom, 64px minimum height).

## §04 Components

"The same five parts on every screen. One primary button per view."

Page 1 shows two of the five parts before the PDF page ends (the page is cut
off; its title is clipped too). The other three are derived from how the
mockups on pages 2–13 draw them, and are marked *(derived)* below.

- **Buttons**
  - `.ds-btn-primary` — Seal fill, white text. **One per view.**
  - `.ds-btn-secondary` — 1px ink outline, transparent fill.
  - `.ds-link` — text link: semibold ink text, tan underline (`ds-underline`).
    See **Links** below for where each link style applies.
  - `.ds-btn-disabled` / `disabled` — `ds-disabled` fill, text-2.
  - All buttons are at least 44px tall with a visible focus outline.
- **Status tags** — `.ds-tag-pass` (✓ Passes), `.ds-tag-fail` (✗ Fails),
  `.ds-tag-review` (! Review), `.ds-tag-neutral` (Adjourned — outline),
  `.ds-tag-active` (Active — ink-2 fill). Always pair colour with an icon or
  word; never colour alone.
- **Inputs** *(derived — Login, Search)* — `.ds-input`: Sheet fill, Rule
  border, 48px tall, ink border on focus. `.ds-label` above, 16px gap.
- **Ruled lists / tables** *(derived — Cases, Deadlines, Compliance)* — a 2px
  ink rule over the header, 1px rules between rows, `.ds-row` heights.
- **Panels** *(derived — Extracted data, Next hearing)* — Sheet fill with a
  1px Rule border for document-like content; Ink fill with paper text for a
  single highlighted fact (e.g. next hearing). 2–4px corners, no shadow.

### Links — decided 2026-09-27, don't re-decide per page

| Where | Class | Look |
|---|---|---|
| **Auth screens only** — Login, Signup, Welcome, Forgot password, Reset password, OTP: their action links ("Forgot password?", "Create an account", "Sign in", "Resend code") | `.ds-link-seal` | Seal text, Seal underline (design page 2) |
| **Everywhere else** — citations and source links, in-content links, secondary navigation ("View all", "Back to cases"), AI answer text | `.ds-link` | Ink text, tan underline (page 1 base rule) |

Seal links are an auth-screen exception: in the app, Seal stays reserved for
the uses listed in §01. Never use `.ds-link-seal` inside `AppShell`.

Recurring patterns in the mockups: the ink sidebar with a Seal marker on the
active item and the arch motif at its foot (page 7); ink hero bands with the
arch motif (Login, Landing, Research header); AI output always labelled
("AI summary · AI-generated · read with the original") and ending in its
sources.

## What the mockups show that we don't build

The mockups include features the app doesn't have. **Do not build fake UI
for them** — adapt each page to what exists (decided 2026-09-27):

| Mockup | Adaptation |
|---|---|
| Dashboards, Cases list/detail (pp. 4–6, 8–9) | Remove Calendar, cause list, deadlines, client messages, and the student reading/practice sections. Keep only real data. |
| Research (p. 11) | Remove the jurisdiction and court filters and the "Judgments" source type — the index is statute text only, and these filters were removed for that reason. |
| AI Chat (p. 10) | No "Open at section" deep links — show the source name and excerpt only. |
| Document Analysis (p. 12) | No page references on extracted values — the API has none. |
| Contracts (p. 13) | Only the 3 real templates (NDA, Employment, Service Agreement); no "Export .docx" — no export exists. |
| Login (p. 2) | No "I am a" role picker (login is email + password; the account holds the role) and no English / اردو switch (the interface isn't translated). Hero copy made true: "tied to the statute it came from", "Citations checked against the statute text", "Federal statutes of the Pakistan Code, in one search" (the index has only three provincial Acts). |
| Landing (p. 3) | No Pricing, free trial or "Start your free trial" copy. |

**Copy must stay statute-only.** The mockups say "tied to the statute or
judgment", "searches statutes and reported judgments" etc. Every such line is
rewritten to match the app's existing wording: *"LegalEase's library of
Pakistani statute text (Acts, Ordinances, Codes and Orders) … no court
judgments or case law."*

## Shared components — use these, don't rebuild per page

Being migrated to the tokens above page by page:

- **`frontend/src/components/layout/AppShell.jsx`** — every internal page (sidebar + header + content). Role-aware nav.
- **`frontend/src/layouts/AuthShell.jsx`** — every public auth page (two-pane ink / paper).
- **`frontend/src/components/ui/AppButton.jsx`** — every button and button-styled link.
- **`frontend/src/features/dashboard/components/PanelCard.jsx`** — titled panel.
- **`frontend/src/lib/formStyles.js`** (`cnInput`) — input styling.
- **`frontend/src/lib/Markdown.jsx`** — the single renderer for AI-generated text (`prose prose-ink`).
- **`frontend/src/components/common/ArchPattern.jsx`** — the arch motif (sidebar foot, ink hero bands).

Do not create a second sidebar / header / panel / input / button style —
extend these.

## Migration status

- **Done:** tokens (`ds-` colours, `font-ds-serif` / `font-ds-sans`,
  `rounded-ds`, `max-w-ds-content`), type classes and component classes in
  `frontend/tailwind.config.js` and `frontend/src/index.css`; token test page
  at `/design-system` (not linked from the app).
- **Migrated:** `AppShell` (sidebar, page header, mobile drawer), `AuthShell`
  (ink identity panel shared by all six auth pages), Login.
- **Not yet migrated:** every other page's content (the auth pages other than
  Login keep old-style forms inside the new frame) still uses the previous tokens
  (`paper`, `ink-panel`, `ink-text`, `ink-muted`, `hairline`, `brick`,
  `font-editorial`, `.type-*`). Those tokens are **deprecated** — don't use
  them in new work; they are removed once the last page has moved.
- The `ds-` prefix exists only because the old `paper` (`#F6F1E7`) differs
  from the new Paper (`#F4EFE4`); it can be dropped after migration.

### Orphaned old files (unused; not deleted)
`frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/layouts/AuthLayout.jsx`,
`frontend/src/components/layout/Sidebar.jsx`, `frontend/src/components/layout/DashboardHeader.jsx`,
`frontend/src/features/dashboard/components/DashboardStat.jsx`,
`frontend/src/components/common/GradientBackground.jsx`, `frontend/src/components/common/AnimatedCard.jsx`,
and the shadcn `frontend/src/components/ui/{button,input,label,badge}.jsx` primitives are not imported by any page.
