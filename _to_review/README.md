# Files set aside for review

Moved here during the 2026-10-08 tidy-up (see [docs/archive/TIDY_PLAN.md](../docs/archive/TIDY_PLAN.md)) instead of being
deleted. Each file keeps its original path below this folder. The team decides whether to keep or remove them.

- `docs/architecture/diagrams/Claude.md`: a prompt for rebuilding the project as a MERN/Node/Mongo app. It doesn't match
  this FastAPI/React/PostgreSQL code.
- `backend/faiss_judgments_meta.json`: an untracked copy of `backend/storage/kb/faiss_judgments_dev_meta.json`
  (byte-identical) found at the backend root. No code reads or writes that path. It was moved here on disk and is
  git-ignored (784 KB of data), so it isn't in git.
