"""Run the 78-question lawyer QA eval set through the live
/api/v1/research/search endpoint and report the top relevance score per
question, plus the distribution across score bands, against the app's
RAG_SIMILARITY_THRESHOLD.

Needs the backend running. From the project root, with the backend venv:

    python scripts/eval_research_retrieval.py              # all questions
    python scripts/eval_research_retrieval.py --limit 5    # quick check, writes nothing
    python scripts/eval_research_retrieval.py --out my.json

Authentication, in order:
  1. LEGALEASE_TOKEN: an access token (e.g. copied from a login response).
  2. Otherwise a throwaway account is created (eval.<time>@example.com,
     student role), its signup code is read from the database, and the
     account and its rows are deleted again when the script ends, even if
     it fails.

Every question costs one Groq call (the query rewrite), about 400 tokens.
LEGALEASE_API overrides the API base URL (default http://127.0.0.1:8000/api/v1).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
QA_CSV = ROOT / "data" / "processed" / "qa_eval" / "Legal_QA_dataset_From_lawyers_clean.csv"
DEFAULT_OUT = ROOT / "data" / "processed" / "qa_eval" / "retrieval_eval_results.json"
BASE_URL = os.environ.get("LEGALEASE_API", "http://127.0.0.1:8000/api/v1").rstrip("/")


def _backend():
    """The backend's settings and database engine (reads backend/.env)."""
    sys.path.insert(0, str(BACKEND))
    cwd = os.getcwd()
    os.chdir(BACKEND)  # settings read .env relative to the working directory
    try:
        from app.core.config import settings
        from app.db.session import engine
    finally:
        os.chdir(cwd)
    return settings, engine


class ThrowawayAccount:
    """A student account that exists only for this run."""

    def __init__(self, engine):
        self.engine = engine
        self.email = f"eval.{int(time.time())}.{secrets.token_hex(3)}@example.com"
        self.password = secrets.token_urlsafe(16)
        self.user_id = None

    def create(self) -> str:
        from sqlalchemy import text

        r = requests.post(f"{BASE_URL}/auth/signup", timeout=30, json={
            "full_name": "Retrieval Eval (temporary)", "email": self.email,
            "password": self.password, "role": "student",
        })
        if r.status_code not in (200, 201, 202):
            raise RuntimeError(f"signup failed: {r.status_code} {r.text[:200]}")
        with self.engine.connect() as c:
            row = c.execute(text("select id, otp from users where email = :e"), {"e": self.email}).one()
        self.user_id = row.id
        r = requests.post(f"{BASE_URL}/auth/verify-email", json={"email": self.email, "otp": row.otp}, timeout=30)
        r.raise_for_status()
        r = requests.post(f"{BASE_URL}/auth/login", json={"email": self.email, "password": self.password}, timeout=30)
        r.raise_for_status()
        print(f"Using throwaway account {self.email}")
        return r.json()["tokens"]["access_token"]

    def delete(self) -> None:
        """Remove the account and every row it produced, in one transaction."""
        from sqlalchemy import text

        if self.user_id is None:
            with self.engine.connect() as c:
                self.user_id = c.execute(text("select id from users where email = :e"), {"e": self.email}).scalar()
        if self.user_id is None:
            return
        with self.engine.begin() as c:
            p = {"u": self.user_id}
            c.execute(text("delete from chat_messages where session_id in (select id from chat_sessions where user_id = :u)"), p)
            c.execute(text("delete from chat_sessions where user_id = :u"), p)
            c.execute(text("delete from activity_logs where user_id = :u or entity_id = :u"), p)
            for table in ("students", "clients", "lawyers"):
                c.execute(text(f"delete from {table} where user_id = :u"), p)
            c.execute(text("delete from users where id = :u"), p)
        print(f"Deleted throwaway account {self.email}")


def load_questions() -> list[str]:
    with QA_CSV.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r["Query"].strip() for r in rows if r["Query"].strip()]


def bucket(score: float) -> str:
    bounds = [0.0, 0.5, 0.6, 0.65, 0.7, 0.8, 1.01]
    labels = ["<0.5", "0.5-0.6", "0.6-0.65", "0.65-0.7", "0.7-0.8", "0.8+"]
    for i in range(len(bounds) - 1):
        if bounds[i] <= score < bounds[i + 1]:
            return labels[i]
    return "0.8+"


def run(token: str, threshold: float, limit: int | None, out: Path | None) -> None:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    questions = load_questions()
    if limit is not None:
        questions = questions[:limit]
    print(f"{len(questions)} questions from {QA_CSV.name}; threshold {threshold}\n")

    results = []
    for i, q in enumerate(questions, 1):
        resp = requests.post(f"{BASE_URL}/research/search", headers=headers,
                             json={"query": q, "top_k": 1}, timeout=90)
        if resp.status_code != 200:
            print(f"[{i:2d}] ERROR {resp.status_code}: {resp.text[:200]}")
            results.append({"i": i, "query": q, "top_score": None, "error": resp.text[:200]})
            continue
        hits = resp.json().get("results", [])
        top_score = hits[0]["relevance"] if hits else 0.0
        top_title = hits[0]["title"] if hits else None
        passes = top_score >= threshold
        results.append({"i": i, "query": q, "top_score": top_score, "top_title": top_title, "passes": passes})
        print(f"[{i:2d}] {top_score:.4f} ({'PASS' if passes else 'below':5s})  {q[:70].replace(chr(10), ' ')}...")

    scored = [r for r in results if r.get("top_score") is not None]
    if scored:
        dist: dict[str, int] = {}
        for r in scored:
            dist[bucket(r["top_score"])] = dist.get(bucket(r["top_score"]), 0) + 1
        print("\n=== Score distribution ===")
        for b in ["<0.5", "0.5-0.6", "0.6-0.65", "0.65-0.7", "0.7-0.8", "0.8+"]:
            n = dist.get(b, 0)
            print(f"  {b:10s}  {n:3d}  ({100 * n / len(scored):5.1f}%)  {'#' * n}")
        n_pass = sum(1 for r in scored if r["passes"])
        print(f"\n  Total scored: {len(scored)}")
        print(f"  >= {threshold} (chat would answer): {n_pass} ({100 * n_pass / len(scored):.1f}%)")
        print(f"  <  {threshold} (chat would refuse): {len(scored) - n_pass} ({100 * (len(scored) - n_pass) / len(scored):.1f}%)")

    if out is not None:
        out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nPer-question results written to {out}")
    else:
        print("\n(--limit run: results not written; pass --out to save them)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--limit", type=int, help="only the first N questions (results not written unless --out)")
    ap.add_argument("--out", type=Path, help=f"where to write results (default for a full run: {DEFAULT_OUT})")
    args = ap.parse_args()
    out = args.out or (DEFAULT_OUT if args.limit is None else None)

    settings, engine = _backend()
    threshold = settings.RAG_SIMILARITY_THRESHOLD

    token = os.environ.get("LEGALEASE_TOKEN")
    if token:
        print("Using the access token from LEGALEASE_TOKEN")
        run(token, threshold, args.limit, out)
        return 0

    account = ThrowawayAccount(engine)
    try:
        run(account.create(), threshold, args.limit, out)
    finally:
        account.delete()
    return 0


if __name__ == "__main__":
    sys.exit(main())
