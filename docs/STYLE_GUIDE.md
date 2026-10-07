# Style Guide — Design system v1 (2026)

> Referenced by `docs/archive/PROJECT_CONTEXT.md`: "Follow the style rules in
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
the uses listed in §01. Never use `.ds-link-seal` inside `AppShell`. The
Landing page's closing "Already have an account? Sign in" uses it too, so the
sign-in link looks the same wherever a signed-out visitor meets it.

**Sign in / sign up wording — decided 2026-09-28.** Across Landing, Login,
Welcome, Signup and Forgot password the two actions are always worded
exactly **"Sign in"** and **"Create an account"**:

| Where | Element |
|---|---|
| Landing nav | "Sign in" — outlined secondary button on ink (`.ds-btn-secondary-on-ink`) |
| Landing hero and closing | "Create an account" — the view's one Seal primary button, to the Welcome role choice |
| Prompts under forms and on Landing's close | "Already have an account? / Remembered your password? **Sign in**", "New to LegalEase? **Create an account**" — `.ds-link-seal` |
| Welcome heading, Signup heading and submit | "Create an account" |

Every "Create an account" goes to Welcome (`/welcome`): Signup reads the role
chosen there (`?role=`) and would otherwise default to client.

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
| Dashboards, Cases list/detail (pp. 4–6, 8–9) | Remove Calendar, cause list, deadlines, client messages, and the student reading/practice sections. Keep only real data. Cases: no Next hearing / Client columns ("Updated" instead), no issues framed, next-hearing panel, Research/Notes tabs or "Ask about this case"; the primary action is the real status change. No status shows in Seal (no due dates exist). |
| Research (p. 11) | Remove the jurisdiction and court filters and the "Judgments" source type — the index is statute text only, and these filters were removed for that reason. No "Summarise top results with AI" (not built). Passage analysis runs on request, not on open; its "judgment" field is labelled "Operative rule". *Update 2026-10-06 (kb-v2, branch only):* category, jurisdiction, source tier and year filters were added at the user's request; they apply only to passages whose law's metadata is known, and the page says how many documents that covers. |
| AI Chat (p. 10) | No "Open at section" deep links — show the source name and excerpt only. No scope / linked-case tags, "Save to case" or attach button (not built). Meta line counts statutes; "No unverified section references" is derived from the backend citation check's "(unverified)" flags. |
| Document Analysis (p. 12) | No page references on extracted values — the API has none. No "View original" (no download endpoint), no breadcrumb or document list (one document per visit). Summary's own risk section is dropped when its risks are shown as Points to review rows. |
| Contracts (p. 13) | Only the 3 real templates (NDA, Employment, Service Agreement); no "Export .docx" — no export exists. No "Fix failing item"; the compliance check is the backend's keyword check — pass/fail only, no review state. |
| Login (p. 2) | No "I am a" role picker (login is email + password; the account holds the role) and no English / اردو switch (the interface isn't translated). Hero copy made true: "tied to the statute it came from", "Citations checked against the statute text", "Pakistani Acts, Ordinances and Codes, in one search". |

**Corpus wording (2026-09-28):** describe the library as "about N Pakistani
legal documents" (N live from `/research/stats`), "mostly Acts, Ordinances,
Codes and Orders" where more detail helps. Never name a source for it (e.g.
"the Pakistan Code") — the raw datasets' provenance isn't recorded — *(Exception, kb-v2 Knowledge Base page, user decision 2026-10-06: it labels records "LegalEase corpus (Pakistan Code-derived)" and shows the Pakistan Code notice; it never calls them official text.)* and
don't call all of it "statutes": it includes ESTACODE, a civil-service manual
(see `docs/corpus_statute_list.md`).
| Landing (p. 3) | No Pricing, free trial or "Start your free trial" copy. |

**Copy must stay statute-only.** The mockups say "tied to the statute or
judgment", "searches statutes and reported judgments" etc. Every such line is
rewritten to match the app's existing wording: *"LegalEase's library of
Pakistani statute text (Acts, Ordinances, Codes and Orders) … no court
judgments or case law."*

## Shared components — use these, don't rebuild per page

- **`frontend/src/components/layout/AppShell.jsx`** — every internal page (sidebar, page header, optional ink `band`, full-height `bare` mode). Role-aware nav.
- **`frontend/src/layouts/AuthShell.jsx`** — every public auth page (two-pane ink / paper; `heroAlign`).
- **Buttons, inputs, tags, links** — the `ds-` classes in `frontend/src/index.css` (`.ds-btn-primary`, `.ds-btn-secondary`, `.ds-btn-secondary-on-ink`, `.ds-input`, `.ds-label`, `.ds-tag-*`, `.ds-link`, `.ds-link-seal`). There is no button or input component — use the classes.
- **`frontend/src/lib/Markdown.jsx`** — the single renderer for AI-generated text (`variant="ds"` → `prose prose-ds`, `.ds-cite` markers).
- **`frontend/src/components/common/Wordmark.jsx`** — the arch mark + "LegalEase AI" wordmark.
- **`frontend/src/components/common/ArchPattern.jsx`** — `ArchOutlines` (auth panel, Landing hero).
- **`frontend/src/features/dashboard/components/DashParts.jsx`** — figure row, ruled sections, AI-chat list for dashboards.
- **`frontend/src/features/document-analysis/UploadStrip.jsx`** — the dashed drag-and-drop upload strip.
- **`frontend/src/features/case-management/StatusTag.jsx`** + `caseMeta.js` — case status tags, type labels, readable timeline wording.

Do not create a second sidebar / header / panel / input / button style —
extend these.

## Migration status

- **Done:** tokens (`ds-` colours, `font-ds-serif` / `font-ds-sans`,
  `rounded-ds`, `max-w-ds-content`), type classes and component classes in
  `frontend/tailwind.config.js` and `frontend/src/index.css`. (The
  `/design-system` token test page was removed before the demo, 2026-09-28.)
- **Migrated:** `AppShell` (sidebar, page header, mobile drawer), `AuthShell`
  (ink identity panel shared by all six auth pages), Login, AI Chat
  (incl. `prose-ds` for AI output, `.ds-cite` markers, the Short answer box),
  Documents, Cases list, Case detail, Research (search + passage), Dashboards (lawyer, client, student), Contracts (list, drafting, contract page), Landing, the forms inside all six auth screens, and the 404 page (`NotFoundPage`).
- **Migration complete (2026-10-04).**
  - `ComingSoonPage.jsx` and its eight placeholder routes were removed, so
    nothing used the previous theme any more.
  - The previous tokens are gone from `tailwind.config.js` and `index.css`:
    `paper`, `ink-*`, `hairline`, `brick`, `legal-*`, the shadcn colour
    variables, `font-editorial` / Inter / Playfair, `.type-*`, the `ink`
    prose theme, gradients and animations.
  - The base layer uses design-system tokens (body `ds-paper` / `ds-text` /
    IBM Plex Sans, default border `ds-rule`).
  - `index.html` loads only Newsreader and IBM Plex Sans.
- **The `ds-` prefix** exists only because the old `paper` (`#F6F1E7`)
  differed from the new Paper (`#F4EFE4`). Now that the old tokens are
  gone, it could be dropped in a rename-only change. That hasn't been done,
  because it would touch every page.

### Old files removed (2026-09-28)
The pre-v1 components no page imported any more — old layouts, sidebar,
header, navbar/footer, stat/feature cards, `AppButton`, `PanelCard`,
`formStyles` (`cnInput`), the shadcn `ui/*` primitives and `lib/utils` —
were deleted, along with the unused mock research data
(`legal-research/data.js`, fabricated judgment citations).
