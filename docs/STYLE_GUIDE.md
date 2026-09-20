# Style Guide — Editorial redesign (2026)

> Referenced by `Project_Context.md`: "Follow the style rules in
> STYLE_GUIDE.md exactly — do not improvise colors, fonts, or spacing."
> This file is that reference. The whole app has now been converted — see
> "Conversion status" at the bottom.

## Palette

| Token (Tailwind) | Hex | Use |
|---|---|---|
| `paper` | `#F6F1E7` | Page background — every page, no exceptions |
| `ink-panel` | `#1E2E28` | The `AppShell`/`AuthShell` sidebar/hero panel, and solid primary-action buttons. Not used as a decorative section background anywhere else (e.g. the landing page's final CTA stays on `paper`, not a dark band). |
| `ink-text` | `#241F1A` | Primary text |
| `ink-muted` | `#6B6255` | Secondary / muted text |
| `hairline` | `#C9BFA8` | Strong dividers — structural separations |
| `hairline-subtle` | `#E4DCC9` | Subtle dividers — between repeating list rows |
| `brick` | `#7A3226` | Accent — **sparing use only**: small text links, citation markers. **Never** a solid button fill or background. Also the "urgent" status color (same hex, deliberately). |
| `status-active` | `#3E6E52` | Status dot — active/green |
| `status-pending` | `#B08B3C` | Status dot — pending/amber |
| `status-urgent` | *(use `brick`)* | Status dot — urgent/red. Same hex as the accent — error text and urgent dots both just use `brick`. |

Defined in `frontend/tailwind.config.js` under `theme.extend.colors`, additive to the old `legal.*` tokens (now unused — see "Orphaned old files" below).

**The one-accent rule:** `brick` is for small text links (e.g. "Forgot password?", "Get started", "View all", citation markers), never a solid button/fill/badge/background. Primary actions are solid `ink-panel` background with `paper` text.

## Typography

- **Serif** (`font-editorial` → Georgia, Times New Roman, serif) — headings, greetings, identity moments only. Page titles, section/panel titles, the auth-page hero heading. Never body text, labels, buttons, or nav.
- `font-editorial` is **bold (weight 700) at the CSS level** — set once in `index.css` (`.font-editorial { font-weight: 700; }`) so every serif heading, present and future, gets real weight contrast against body text with no risk of a page forgetting `font-bold`.
- **Sans** (`font-sans` → Inter) — everything else: body text, labels, inputs, nav, buttons, stat values.
- **Sentence case everywhere.** No `uppercase` labels anywhere in the app, no exceptions.
- `font-editorial` is deliberately a separate Tailwind key from the old `font-serif` (Playfair Display) — the old key is now unused.

## Components

- **No rounded-card-with-shadow grids.** Flat sections + hairline dividers only. No `shadow-*`, no `rounded-xl`/`rounded-2xl` content containers (small `rounded-full` status dots and avatar circles are fine — that's a dot/avatar convention, not a "card").
- **Buttons have real presence.** Shared component: `AppButton` (`frontend/src/components/ui/AppButton.jsx`) — always use it instead of a raw `<button>`/styled `<Link>`. Fixed padding `py-3 px-7` (12px vertical / 28px horizontal), `rounded-md` (6px radius). `variant="primary"` (default): solid `bg-ink-panel` fill, `text-paper`, `hover:bg-ink-panel/85`. `variant="secondary"`: `border border-hairline`, transparent fill, `hover:bg-hairline-subtle/50`. `brick` is never a button fill — see the one-accent rule above. Pass `to` for a router link or omit it for a native `<button>`.
- **Inputs are underline-style**: `border-0 border-b border-hairline`, transparent background. Shared helper: `cnInput()` in `frontend/src/lib/formStyles.js` — always use it instead of restyling inputs by hand. Focus deepens the underline to `ink-text` **and** adds a subtle background tint (`focus:bg-ink-text/[0.03]`); error state switches the underline to `brick` with its own tint (`bg-brick/[0.04]`).
- **Sidebar nav**: `bg-ink-panel`, icon + label rows, `text-paper/60` default → `text-paper` + `bg-paper/10` active/hover. Never `brick` for the active state — nav selection is not a "text link."
- **List rows / stat strips**: `border-b border-hairline-subtle` between rows, `border-r border-hairline` between stat-strip columns — never boxed cards. **Rows that are clickable (case rows, session rows, quick actions, etc.) get a subtle hover tint** — `hover:bg-hairline-subtle/40` on the row's own link/button (with small negative-margin padding, e.g. `px-2 -mx-2`, so the tint doesn't shift layout) — never `hover:text-brick`. Accent is for standalone text links only, never for anything that behaves like a button or a row.
- **Status**: a small colored dot + sentence-case text, never a colored pill/badge/chip. Don't force a state into "urgent" (`brick`) just because it needs *a* color — a neutral/terminal state (e.g. "Closed") can just use `ink-muted`.
- **Equally-weighted option lists** (quick actions, etc.): a single-column hairline-`subtle`-divided list (icon + label), not a grid of filled/bordered buttons.
- **AI Chat citations**: numbered superscript footnote markers inline in the answer text (`.citation-marker` class in `index.css`, colored `brick`), linking down to a small numbered list below the message. Never badges/chips.
- **Divider hierarchy**: `hairline` for structural separations (header bottom edge, panel title→body, stat-strip columns, section boundaries on the landing page). `hairline-subtle` for repeating rows within one list.
- **Arch-silhouette background motif** — Login and the landing-page hero **only**. Shared component: `frontend/src/components/common/ArchPattern.jsx`, a tileable SVG `<pattern>` of a pointed-arch silhouette (courthouse/Mughal-arch evocation), colored via `currentColor` so the caller controls color/opacity with Tailwind classes (`text-paper opacity-[0.08]` on the dark auth panel, `text-ink-panel opacity-[0.07]` behind the landing hero). Always low-opacity (6–15%) and always behind real content (`relative z-10` on the foreground) so legibility is never affected. `AuthShell` exposes this as an opt-in `showArch` prop (default `false`) rather than a redesign — only `LoginPage` passes it.

## Shared components — use these, don't rebuild per page

- **`frontend/src/components/layout/AppShell.jsx`** — every internal (authenticated) page. Sidebar + header + main content. Role-aware nav (`ROLES.LAWYER`/`CLIENT`/`STUDENT`) and workspace label baked in. Props: `title`, `subtitle`, `headerActions` (optional, e.g. a search box), `children`.
- **`frontend/src/layouts/AuthShell.jsx`** — every public auth page (Login, Welcome, Signup, Forgot Password, OTP, Reset Password). The two-pane ink-panel hero / paper form split. Props: `heroTitle`, `heroSubtitle`, `tagline`, `children`.
- **`frontend/src/features/dashboard/components/PanelCard.jsx`** — flat titled panel (serif title, muted description, hairline divider, content). Same import path as the old version, so nothing needed re-importing.
- **`frontend/src/lib/formStyles.js`** (`cnInput`) — underline input styling, shared by every form.
- **`frontend/src/components/common/{Logo,StatCard,FeatureCard}.jsx`** — fixed in place to the new flat look (no gradient tiles, no rounded shadowed cards). Same import paths.
- **`frontend/src/components/ui/AppButton.jsx`** — every button/button-styled-link app-wide. See "Buttons have real presence" above.
- **`frontend/src/components/common/ArchPattern.jsx`** — the arch-silhouette background motif. Login + landing hero only.

Do not create a second sidebar/header/panel/input/button style — extend these instead.

## Conversion status

**Every page is now converted**, including a second stricter pass that added: bold serif headings, the shared `AppButton` component (fixed 12px/28px padding, 6px radius, real hover states) replacing every raw button/link across the app, input focus/error background tints, subtle hover tints on every clickable list/table row (replacing an earlier `hover:text-brick` pattern that violated the "accent is never a button" rule), and the arch-silhouette motif behind Login and the landing hero.

Auth pages (`AuthShell`): Login (reference page — only additive changes: `AppButton` on submit, `showArch`), Welcome, Signup (rebuilt — see below), Forgot Password, OTP Verification, Reset Password.
Internal pages (`AppShell`): Lawyer Dashboard, Client Dashboard, Student Dashboard, Case List, Case Detail, Documents, Legal Research (+ detail), AI Assistant, and the `ComingSoonPage` placeholder (covers Clients, Contracts, Schedule, Profile, Notifications).
Public: Landing page — restructured to exactly 6 sections: nav, hero (exact one-line subheadline + arch motif), stats strip (3 numbers), "How answers are grounded" 4-step pipeline, 3-column feature grid (Case management / Document analysis / Practice simulator), final CTA. `AICapabilities.jsx`, `LegalServices.jsx`, and `Testimonials.jsx` were deleted (not just unlinked) as superseded by this structure — safe given they were git-tracked and the repo has history to recover them from if needed.

### Signup form — simplified, with a known backend gap

`SignupPage.jsx` now collects exactly 6 fields for every role (Lawyer/Client/Student): full name, email, phone number, password, confirm password, role. Bar license number, CNIC, university ID, and other role-specific fields were removed — no verification system exists for them yet.

**This does not yet match the backend.** `backend/app/schemas/auth.py`'s `SignupRequest` discriminated union still requires `bar_license_no`/`specialization`/`bar_year` for Lawyer and `university_id`/`university_name`/`current_year` for Student. Since this pass was frontend-only, **Lawyer and Student signup will 422 against the current backend** until the backend schema is relaxed to match (Client signup is unaffected — it never required extra fields). This is a real functional gap, not just a style note — flagging until the backend is updated.

### Orphaned old files (not deleted, just unused — flagging, not fixing without being asked)
`frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/layouts/AuthLayout.jsx`, `frontend/src/components/layout/Sidebar.jsx` (old), `frontend/src/components/layout/DashboardHeader.jsx`, `frontend/src/features/dashboard/components/DashboardStat.jsx`, `frontend/src/components/common/GradientBackground.jsx`, `frontend/src/components/common/AnimatedCard.jsx`, and the shadcn `frontend/src/components/ui/{button,input,label,badge}.jsx` primitives are no longer imported by any page. Left in place rather than deleted since deletion wasn't asked for in this pass — worth a cleanup pass later.
