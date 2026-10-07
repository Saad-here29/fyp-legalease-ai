# Frontend

React 19 + Vite single-page app for LegalEase AI. It uses design system v1,
described in [`docs/architecture/STYLE_GUIDE.md`](../docs/architecture/STYLE_GUIDE.md).

## Install and run

```powershell
npm install
copy .env.example .env     # VITE_API_BASE_URL, VITE_API_TIMEOUT_MS
npm run dev                # http://localhost:5173 (proxies /api to http://localhost:8000)
```

The backend must be running too; see the root [`README.md`](../README.md).

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Production build to `dist/` (no source maps; vendor code split into chunks) |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint, zero warnings allowed |
| `npm run format` | Prettier |

There are no frontend tests yet.

## How it's organised

- **`src/routes/AppRouter.jsx`:** every route. Pages for signed-in users are
  wrapped in `ProtectedRoute`, which checks the role and sends users to
  their own dashboard. Unknown addresses show `NotFoundPage`.
- **`src/features/<feature>/`:** each feature has its pages, components and
  an `api.js`. Endpoint paths live in `src/api/endpoints.js`, and the Axios
  client in `src/api/client.js`. The client sends the auth cookies and
  refreshes the session on a 401.
- **`src/components/layout/AppShell.jsx`:** the signed-in page frame
  (sidebar, header, mobile drawer). Auth pages use `src/layouts/AuthShell.jsx`.
- **Styling:**
  - Tailwind with the design-system tokens in `tailwind.config.js` (`ds-`
    colours, Newsreader and IBM Plex Sans);
  - component classes (`ds-btn-primary`, `ds-h1`, …) in `src/index.css`;
  - AI-generated text renders through `src/lib/Markdown.jsx` with
    `prose-ds`.
- **State:**
  - the signed-in user is in a Zustand store (`src/store/authStore.js`);
  - server data is cached with TanStack Query.
