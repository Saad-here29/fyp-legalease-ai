# Scraping: post-mock merge checklist

Do this **after** the mock presentation, and only with approval. Every step
is reversible until step 5; steps 5 and 6 touch the shared database.

## 0. Before you start

- [ ] **Approval to merge.**
- [ ] **Main folder clean,** on `master`, in sync with `origin/main`:
  `git status`, `git fetch`, `git log -1`.
- [ ] **A database backup or snapshot** taken in Supabase (Database →
  Backups), or at least an export of `alembic_version`.
- [ ] **No demo running** against the database.

## 1. Bring the branch up to date (in the worktree)

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-scraping
git fetch origin
git merge origin/main          # or: git rebase origin/main
```

- [ ] **No conflicts.** The likely spots are `backend/app/models/__init__.py`,
  `backend/app/schemas/research.py`, `backend/app/api/v1/research.py` and
  `frontend/src/features/legal-research/ResearchPage.jsx`.

## 2. Check the Alembic chain against master

```powershell
cd backend
..\..\fyp-legalease-ai-main\backend\venv\Scripts\alembic.exe heads
..\..\fyp-legalease-ai-main\backend\venv\Scripts\alembic.exe history
```

- [ ] **Exactly one head:** `a3c5e7f90b12`.
- [ ] **`a3c5e7f90b12` revises master's latest migration.** As of
  2026-10-06 that's `e7b3c9d14a02`. If master has gained a migration since,
  set `down_revision` in `alembic/versions/a3c5e7f90b12_scraping_tables.py`
  to master's head, re-check that there's one head, and commit.
- [ ] **Re-test up and down on a fresh throwaway schema** (the migration
  test helper, or `alembic -x schema=scrapetest_x upgrade head`, then
  `downgrade -1`, against the session pooler on port 5432). Then drop that
  schema.

## 3. Tests and build on the merged branch

- [ ] **`pytest`:** everything passes. The 26 scraping tests are offline;
  only the NER weight tests skip in a worktree.
- [ ] **`ruff check .`:** no new findings beyond the 21 known ones.
- [ ] **`npm run lint` and `npm run build`:** clean.

## 4. Merge into master

```powershell
cd E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main
git switch master
git merge --no-ff scraping -m "Merge scraping prototype (staged, not indexed)"
git push origin master:main
```

- [ ] **Pushed,** and `git log --oneline -3` shows the merge.

## 5. Apply the migration to the shared database (public schema)

```powershell
cd backend
venv\Scripts\activate
alembic current          # expect e7b3c9d14a02
alembic upgrade head     # applies a3c5e7f90b12: two new tables, nothing existing touched
alembic current          # expect a3c5e7f90b12
```

- [ ] **Exactly two new tables,** `scraped_documents` and `scrape_runs`,
  and the existing tables' row counts are unchanged (compare
  `select count(*)` on users, cases and documents before and after).

## 6. First scraper run against the public schema

The script refuses to write without `--schema` (a prototype guard). For the
public schema, pass `--schema public` once that guard is relaxed. That's a
one-line change; review and commit it separately, after step 5.

- [ ] **Dry run first:**
  `python ..\scripts\scraping\scrape_laws.py --dry-run --limit 5`
- [ ] **Then a small real run:**
  `python ..\scripts\scraping\scrape_laws.py --schema public --limit 5 --out logs\scrape_first.json`
- [ ] **Verify:** `select source_name, status, change_kind, count(*) from
  scraped_documents group by 1, 2, 3;` shows staged and baseline rows only,
  and `scrape_runs` has one row.
- [ ] **No text leaks:** search and chat return exactly what they did before
  (the scraped table isn't read by them). Check with one research search.

## 7. Research page line

- [ ] **Restart the backend.** The stats cache is 60 s, so a restart or a
  minute's wait is enough.
- [ ] **`GET /api/v1/research/stats`** has `updates.available: true`, with
  `last_checked` and per-source counts.
- [ ] **The Research page** shows "Sources checked <date>: …" under the
  library line, at desktop and phone width.
- [ ] **The landing page and student dashboard** (which use the same stats)
  still load.

## 8. Schedule (optional, after a week of manual runs)

- [ ] **Register the weekly task** from `docs/architecture/scraping.md` § "Schedule",
  with `--schema public`.

## Rollback

| If… | Do |
|---|---|
| Tests fail after the merge (before step 5) | `git revert -m 1 <merge commit>` and push; the database is untouched |
| The migration fails half-way | It runs in one transaction, so nothing changes. Fix and retry |
| The tables cause trouble after step 5 | `alembic downgrade e7b3c9d14a02` (drops only the two scraping tables, and their staged rows). Then revert the merge |
| The Research page line misbehaves | It's additive. Revert the `ResearchPage.jsx` hunk, or let `available` stay false; search is unaffected |
| A scraper run misbehaves | Stop the scheduled task. Staged rows are inert; delete by `run_id` if needed |

## Afterwards

- [ ] **Drop the throwaway schema** `scrapelive_1791254533` (only when you
  say so): `DROP SCHEMA "scrapelive_1791254533" CASCADE;`
- [ ] **Remove the worktree:** `git worktree remove ..\legalease-scraping`,
  after confirming everything is merged and pushed.
