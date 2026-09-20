"""Run the 78-question lawyer QA eval set through the live
/api/v1/research/search endpoint (retrieval only) and report the top
relevance score per question plus the distribution across score bands,
to check whether RAG_SIMILARITY_THRESHOLD=0.7 is well-calibrated.

Run from the project root with the backend venv active and the backend
dev server running on :8000:  python scripts/eval_research_retrieval.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
QA_CSV = ROOT / "data" / "processed" / "qa_eval" / "Legal_QA_dataset_From_lawyers_clean.csv"
BASE_URL = "http://127.0.0.1:8000/api/v1"
THRESHOLD = 0.7

TEST_EMAIL = "researcheval@example.com"
TEST_PASSWORD = "TestPass123"


def get_auth_token() -> str:
    """Log in the eval test user, signing it up first if it doesn't exist yet."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json()["tokens"]["access_token"]

    # Not registered yet — sign up, pull the OTP from the backend log, verify.
    requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "full_name": "Research Eval",
            "email": TEST_EMAIL,
            "phone": "+923001234567",
            "password": TEST_PASSWORD,
            "role": "lawyer",
        },
        timeout=15,
    )
    time.sleep(1)
    log_path = Path(r"C:\Users\SAADUL~1\AppData\Local\Temp\backend_groq2.log")
    otp = None
    for line in reversed(log_path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        if f"[DEV OTP] {TEST_EMAIL}" in line:
            otp = line.split("->")[1].strip().split()[0]
            break
    if not otp:
        raise RuntimeError(f"Could not find OTP for {TEST_EMAIL} in {log_path}")

    requests.post(f"{BASE_URL}/auth/verify-otp", json={"email": TEST_EMAIL, "otp": otp}, timeout=15)
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["tokens"]["access_token"]


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


def main() -> int:
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    questions = load_questions()
    print(f"Loaded {len(questions)} questions from {QA_CSV.name}\n")

    results = []
    for i, q in enumerate(questions, 1):
        resp = requests.post(
            f"{BASE_URL}/research/search",
            headers=headers,
            json={"query": q, "top_k": 1},
            timeout=60,
        )
        if resp.status_code != 200:
            print(f"[{i:2d}] ERROR {resp.status_code}: {resp.text[:200]}")
            results.append({"i": i, "query": q, "top_score": None, "error": resp.text[:200]})
            continue
        data = resp.json()
        hits = data.get("results", [])
        top_score = hits[0]["relevance"] if hits else 0.0
        top_title = hits[0]["title"] if hits else None
        passes = top_score >= THRESHOLD
        results.append({"i": i, "query": q, "top_score": top_score, "top_title": top_title, "passes": passes})
        flag = "PASS" if passes else "below"
        qshort = q[:70].replace("\n", " ")
        print(f"[{i:2d}] {top_score:.4f} ({flag:5s})  {qshort}...")

    # ---- Distribution ----
    scored = [r for r in results if r.get("top_score") is not None]
    dist: dict[str, int] = {}
    for r in scored:
        b = bucket(r["top_score"])
        dist[b] = dist.get(b, 0) + 1

    order = ["<0.5", "0.5-0.6", "0.6-0.65", "0.65-0.7", "0.7-0.8", "0.8+"]
    print("\n=== Score distribution ===")
    for b in order:
        n = dist.get(b, 0)
        pct = 100 * n / len(scored) if scored else 0
        print(f"  {b:10s}  {n:3d}  ({pct:5.1f}%)  {'#' * n}")

    n_pass = sum(1 for r in scored if r["passes"])
    n_fail = len(scored) - n_pass
    print(f"\n  Total scored: {len(scored)}")
    print(f"  >= {THRESHOLD} (chat would answer): {n_pass} ({100*n_pass/len(scored):.1f}%)")
    print(f"  <  {THRESHOLD} (chat would refuse): {n_fail} ({100*n_fail/len(scored):.1f}%)")

    out_path = ROOT / "data" / "processed" / "qa_eval" / "retrieval_eval_results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull per-question results written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
