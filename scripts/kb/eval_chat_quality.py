"""Offline evaluation for the Oct 2026 chat-quality steps.

Three question sets:
  review    the 8 family-law questions from the 2026-10-05 legal review
            (docs/evaluation/chat_review_family_law_2026-10-05.md), with the statutes a
            correct answer should rest on;
  lawyers   the 78 lawyer questions (data/processed/qa_eval/, read-only);
  offtopic  O01-O15 from docs/evaluation/retrieval_gold_set_draft.md (must be refused).

Two commands, run from the project root with the backend venv:

  record  Rewrites every question once with the backend's own rewrite code
          (v1 = the old prompt at temperature 0.3, v2 = the new prompt at 0)
          and saves them. This is the ONLY Groq use: one call per question,
          about 450 tokens. Resumes where it stopped; never falls back to
          another provider; stops on the first failed call.

            python scripts/kb/eval_chat_quality.py record --arm v2 --out docs/evaluation/chat_quality/rewrites_v2.json

  replay  Runs retrieval offline on saved rewrites, through the chat's own
          retrieve_passages(), and writes what each question would get.
          No Groq calls.

            python scripts/kb/eval_chat_quality.py replay --rewrites docs/evaluation/chat_quality/rewrites_v2.json --out ...

  compare Prints per-question gains and losses between two replays.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
QA_CSV = ROOT / "data" / "processed" / "qa_eval" / "Legal_QA_dataset_From_lawyers_clean.csv"
GOLD_MD = ROOT / "docs" / "evaluation" / "retrieval_gold_set_draft.md"

# Expected support for the review questions: statutes (normalised source-name
# fragments) and, where one exists, the index position of the exact chunk.
REVIEW = [
    ("R1", "Why is the Nikah Nama important in a dower dispute?",
     ["muslimfamilylaws", "familycourts"], [835, 49613, 826, 827, 49602, 49603]),
    ("R2", "A wife claims that her dowry articles remain in the husband's possession after "
           "separation. What remedy may be available?",
     ["familycourts", "dowryandbridal"], [49944, 49943]),
    ("R3", "Can a spouse lawfully retain the other's personal property merely because the "
           "marriage has ended?",
     ["familycourts", "dowryandbridal"], [49944]),
    ("R4", "What is a suit for restitution of conjugal rights?",
     ["familycourts"], [49943, 49917]),
    ("R5", "Why is territorial jurisdiction important in a Family Court case?",
     ["familycourts"], [49910]),
    ("R6", "Can a family-law advocate knowingly present false facts before the court merely "
           "to secure relief for the client?",
     ["legalpractitioners", "pakistanpenalcode"], []),
    ("R7", "A wife files a suit seeking dissolution of marriage, unpaid dower, maintenance and "
           "recovery of dowry articles. The husband denies all allegations and claims that the "
           "wife left the matrimonial home without justification. What should the court determine?",
     ["familycourts", "dissolutionofmuslim", "muslimfamilylaws", "dowryandbridal"], [49943, 49944, 49910]),
    ("R8", "If a wife claims unpaid dower, who must establish the relevant facts?",
     ["muslimfamilylaws", "familycourts"], [835, 49613, 49933]),
]


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_sets(names: list[str]) -> list[dict]:
    out = []
    if "review" in names:
        out += [{"set": "review", "id": i, "question": q} for i, q, _, _ in REVIEW]
    if "lawyers" in names:
        with QA_CSV.open(encoding="utf-8-sig") as f:
            rows = [r["Query"].strip() for r in csv.DictReader(f) if r["Query"].strip()]
        out += [{"set": "lawyers", "id": f"L{n:02d}", "question": q} for n, q in enumerate(rows, 1)]
    if "offtopic" in names:
        for line in GOLD_MD.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\| (O\d\d) \| (.+?) \|", line)
            if m:
                out.append({"set": "offtopic", "id": m.group(1), "question": m.group(2).strip()})
    return out


def _backend():
    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)  # settings read .env relative to the working directory
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


# ---------------------------------------------------------------- record

def record(arm: str, sets: list[str], out: Path, pause: float) -> None:
    _backend()
    from app.ai.client import get_ai_client
    from app.ai.query_rewrite import strip_unasked_statutes

    client = get_ai_client()
    if client.provider != "groq":
        sys.exit(f"Groq is not the active provider ({client.provider}); not recording.")
    client._openai = client._gemini = None  # a fallback model would contaminate the record
    usage = {}
    real_create = client._groq.chat.completions.create

    def counting_create(*a, **kw):
        resp = real_create(*a, **kw)
        usage.update(prompt=resp.usage.prompt_tokens, completion=resp.usage.completion_tokens,
                     finish=resp.choices[0].finish_reason, temperature=kw.get("temperature"))
        return resp

    client._groq.chat.completions.create = counting_create

    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"arm": arm, "items": []}
    assert data["arm"] == arm, f"{out} holds arm {data['arm']}"
    done = {(it["set"], it["id"]) for it in data["items"]}
    todo = [q for q in load_sets(sets) if (q["set"], q["id"]) not in done]
    spent = sum(it["prompt_tokens"] + it["completion_tokens"] for it in data["items"])
    print(f"{len(done)} recorded, {len(todo)} to go; {spent} tokens so far")

    for n, q in enumerate(todo, 1):
        usage.clear()
        t0 = time.perf_counter()
        model_rewrite = client.rewrite_search_query(q["question"], v2=(arm == "v2"))
        ms = int((time.perf_counter() - t0) * 1000)
        if not usage:
            sys.exit(f"Groq call failed at {q['id']} (rewrite fell back to the question). Saved; rerun to resume.")
        rewrite = strip_unasked_statutes(q["question"], model_rewrite) if arm == "v2" else model_rewrite
        data["items"].append({**q, "model_rewrite": model_rewrite, "rewrite": rewrite, "ms": ms,
                              "prompt_tokens": usage["prompt"], "completion_tokens": usage["completion"],
                              "finish": usage["finish"], "temperature": usage["temperature"],
                              "date": time.strftime("%Y-%m-%d %H:%M")})
        spent += usage["prompt"] + usage["completion"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        flag = "" if rewrite == model_rewrite else "  [statute stripped]"
        print(f"[{n}/{len(todo)}] {q['id']} {usage['prompt'] + usage['completion']} tok  {rewrite[:80]}{flag}")
        time.sleep(pause)
    print(f"done; {spent} tokens in this file")


# ---------------------------------------------------------------- replay

def replay(rewrites: Path, out: Path, family: str = "off",
           family_threshold: float | None = None) -> None:
    _backend()
    from app.ai import embeddings
    from app.core.config import settings
    from app.services import legal_chat_service as chat

    embeddings.build_or_load()
    pos = {id(m): i for i, m in enumerate(embeddings._META)}
    text_pos = {}
    for i, m in enumerate(embeddings._META):
        text_pos.setdefault(embeddings.record_text(m), i)
    review = {i: (acts, chunks) for i, _, acts, chunks in REVIEW}
    items = json.loads(rewrites.read_text(encoding="utf-8"))["items"]

    # This process only: "off" is the setup without the family index.
    settings.FAMILY_INDEX = family != "off"
    if family_threshold is not None:
        settings.FAMILY_THRESHOLD = family_threshold

    results = []
    for it in items:
        passages = chat.retrieve_passages(it["question"], it["rewrite"],
                                          family="on" if family == "on" else "auto")
        rows = []
        for p in passages:
            i = text_pos.get(embeddings.record_text(p), pos.get(id(p)))
            rows.append({"pos": i, "source": embeddings.record_source(p),
                         "score": round(float(p.get("relevance", 0)), 4),
                         "via_toc": p.get("via_toc"), "family": p.get("family_window") is not None})
        r = {"set": it["set"], "id": it["id"], "question": it["question"], "rewrite": it["rewrite"],
             "answered": bool(rows), "best": max((x["score"] for x in rows), default=None),
             "top_score_any": round(float(embeddings.search(it["rewrite"], top_k=1)[0]["relevance"]), 4),
             "passages": rows}
        if it["set"] == "review":
            acts, chunks = review[it["id"]]
            on_target = [x for x in rows if any(a in norm(x["source"]) for a in acts)]
            support = sorted({x["pos"] for x in rows if x["pos"] in chunks})
            # GOOD: the exact supporting section is retrieved (for R6, which
            # has no single chunk, any passage of an expected Act).
            # PARTIAL: an expected Act, but not the supporting section.
            good = support if chunks else on_target
            r.update(on_target=len(on_target), off_target=len(rows) - len(on_target),
                     support_chunks=support,
                     status=("GOOD" if good else "PARTIAL" if on_target
                             else "OFF-TARGET" if rows else "REFUSED"))
        else:
            r["status"] = "ANSWERED" if rows else "REFUSED"
        results.append(r)
        print(f"{r['id']:4} {r['status']:10} best={r['best']}  {', '.join(sorted({x['source'][:30] for x in rows}))[:110]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rewrites": str(rewrites), "family": family,
                               "threshold": settings.RAG_SIMILARITY_THRESHOLD,
                               "family_threshold": settings.FAMILY_THRESHOLD, "results": results},
                              ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- answer

def answer(rewrites: Path, out: Path, prompt: str, family: str, ids: list[str] | None,
           pause: float) -> None:
    """Generate answers (Groq) for the review questions with the old or the
    strict prompt, on identical passages. Resumes; stops on the first
    failure. About 3,000-4,500 tokens per answered question."""
    _backend()
    from app.ai import embeddings
    from app.ai.client import get_ai_client
    from app.core.config import settings
    from app.services import legal_chat_service as chat

    client = get_ai_client()
    if client.provider != "groq":
        sys.exit(f"Groq is not the active provider ({client.provider}).")
    client._openai = client._gemini = None
    usage = {}
    real_create = client._groq.chat.completions.create

    def counting_create(*a, **kw):
        resp = real_create(*a, **kw)
        usage.update(prompt=resp.usage.prompt_tokens, completion=resp.usage.completion_tokens,
                     finish=resp.choices[0].finish_reason)
        return resp

    client._groq.chat.completions.create = counting_create
    settings.FAMILY_INDEX = family != "off"
    embeddings.build_or_load()

    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"prompt": prompt, "items": []}
    done = {it["id"] for it in data["items"]}
    items = [it for it in json.loads(rewrites.read_text(encoding="utf-8"))["items"]
             if it["set"] == "review" and it["id"] not in done and (not ids or it["id"] in ids)]
    for it in items:
        passages = chat.retrieve_passages(it["question"], it["rewrite"],
                                          family="on" if family == "on" else "auto")
        rec = {"id": it["id"], "question": it["question"], "rewrite": it["rewrite"],
               "passages": [{"n": i + 1, "source": embeddings.record_source(p),
                             "score": round(float(p.get("relevance", 0)), 4),
                             "text": embeddings.record_text(p)} for i, p in enumerate(passages)]}
        if not passages:
            rec.update(answer=None, refused=True, tokens=0)
        else:
            usage.clear()
            lang = chat._detect_language(it["question"])
            try:
                checked = chat.compose_answer(client, passages, [{"role": "user", "content": it["question"]}],
                                              lang, strict=(prompt == "strict"))
            except Exception as e:  # noqa: BLE001
                sys.exit(f"Groq call failed at {it['id']}: {e}. Saved; rerun to resume.")
            rec.update(answer=checked.text, refused=False, citation_check=checked.summary(),
                       tokens=usage.get("prompt", 0) + usage.get("completion", 0),
                       finish=usage.get("finish"))
        data["items"].append(rec)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{it['id']} {'refused' if rec['refused'] else 'answered'} {rec['tokens']} tok")
        if not rec["refused"]:
            time.sleep(pause)
    print("total tokens:", sum(i["tokens"] for i in data["items"]))


# ---------------------------------------------------------------- compare

def compare(a: Path, b: Path) -> None:
    ra = {(r["set"], r["id"]): r for r in json.loads(a.read_text(encoding="utf-8"))["results"]}
    rb = {(r["set"], r["id"]): r for r in json.loads(b.read_text(encoding="utf-8"))["results"]}
    for s in ("review", "lawyers", "offtopic"):
        keys = [k for k in ra if k[0] == s and k in rb]
        if not keys:
            continue
        ca = {}
        for k in keys:
            ca.setdefault((ra[k]["status"], rb[k]["status"]), []).append(k[1])
        print(f"\n== {s} ({len(keys)})")
        for (sa, sb), ids in sorted(ca.items()):
            mark = "" if sa == sb else "   <-- changed"
            print(f"  {sa:10} -> {sb:10} {len(ids):3}  {' '.join(ids) if sa != sb or s != 'lawyers' else ''}{mark}")
        if s == "lawyers":
            changed_src = [k[1] for k in keys if ra[k]["status"] == rb[k]["status"] == "ANSWERED"
                           and {x["source"] for x in ra[k]["passages"]} != {x["source"] for x in rb[k]["passages"]}]
            print(f"  answered in both, different statutes: {len(changed_src)}  {' '.join(changed_src)}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp1252 consoles
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--arm", choices=["v1", "v2"], required=True)
    r.add_argument("--sets", default="review,lawyers,offtopic")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--pause", type=float, default=6.0, help="seconds between calls (Groq's per-minute cap)")
    p = sub.add_parser("replay")
    p.add_argument("--rewrites", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--family", choices=["off", "auto", "on"], default="off")
    p.add_argument("--family-threshold", type=float, default=None)
    a = sub.add_parser("answer")
    a.add_argument("--rewrites", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--prompt", choices=["old", "strict"], required=True)
    a.add_argument("--family", choices=["off", "auto", "on"], default="off")
    a.add_argument("--ids", default="", help="comma-separated review ids, e.g. R3,R6")
    a.add_argument("--pause", type=float, default=45.0)
    c = sub.add_parser("compare")
    c.add_argument("a", type=Path)
    c.add_argument("b", type=Path)
    args = ap.parse_args()
    for attr in ("out", "rewrites", "a", "b"):
        if getattr(args, attr, None) is not None:
            setattr(args, attr, getattr(args, attr).resolve())
    if args.cmd == "record":
        record(args.arm, args.sets.split(","), args.out, args.pause)
    elif args.cmd == "replay":
        replay(args.rewrites, args.out, args.family, args.family_threshold)
    elif args.cmd == "answer":
        answer(args.rewrites, args.out, args.prompt, args.family,
               [x for x in args.ids.split(",") if x], args.pause)
    else:
        compare(args.a, args.b)


if __name__ == "__main__":
    main()
