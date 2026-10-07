"""One file-staging scraping run (kb-v2 C3): fetch, validate, stage, log.

    run(sources, fetcher, caps={...}, budget=900)

Per source, in order: the priority items first (for Pakistan Code: the Acts
its category listings name that we don't hold), then the source's listing
pages, until the source's cap of documents. For each document: page ->
PDF -> text, both saved unchanged (stage.save_original); then

    same URL, same text as last time       -> unchanged
    a core law, or text staged earlier     -> already held (skipped)
    fails validation                       -> quarantined (never indexed)
    otherwise                              -> new / changed, records staged

Resumable: a URL fetched in the last `skip_within_hours` is skipped (it
still counts toward the cap), so running the same command again after a
budget stop or a crash continues where it stopped. The weekly run uses a
shorter window than a week, so every document is checked once a week.
One update-log line per source per run (stage.append_log).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

import requests

from app.scraping import stage
from app.scraping.fetcher import DisallowedError, Fetcher, LimitReachedError
from app.scraping.parse import find_pdf_url, parse_listing

COUNTS = ("fetched", "new", "changed", "unchanged", "already_held", "quarantined", "errors", "skipped_recent")


class BudgetSpent(Exception):  # noqa: N818
    pass


def _recent(entry: dict | None, hours: float) -> bool:
    if not entry or not hours or not entry.get("fetched_at"):
        return False
    try:
        at = datetime.strptime(entry["fetched_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) - at < timedelta(hours=hours)


def _held_by(state: dict, url: str, h: str, run_id: str) -> tuple[str, str] | None:
    """(other URL, its run) whose staged text has this hash, if any."""
    for other, e in state.items():
        if other != url and e.get("hash") == h and e.get("outcome") in ("new", "changed", "unchanged"):
            return other, e.get("run_id") or ""
    return None


def process(item: stage.Item, fetcher: Fetcher, src: dict, state: dict, counts: dict, run_id: str,
            seen_this_run: dict[str, str], log: Callable[[str], None]) -> dict:
    """Fetch and stage one document. Returns its outcome row."""
    source = item.source
    fetched_at = stage.utcnow()
    if src.get("item_is_pdf"):
        item.pdf_url = item.pdf_url or item.url
    else:
        page = fetcher.get(item.url)
        stage.save_original(source, page.url, page.content, page.content_type, "page", fetched_at)
        item.pdf_url = find_pdf_url(page.content, page.url, src)
        if not item.pdf_url:
            raise ValueError("no PDF link on the document page")
    pdf = fetcher.get(item.pdf_url, pdf=True)
    if "pdf" not in pdf.content_type.lower() and pdf.content[:4] != b"%PDF":
        raise ValueError(f"not a PDF ({pdf.content_type})")
    original = stage.save_original(source, pdf.url, pdf.content, pdf.content_type, "pdf", fetched_at,
                                   requested_url=item.pdf_url)
    counts["fetched"] += 1
    return decide(item, src["content_type"], pdf.content, original, fetched_at, state, counts, run_id,
                  seen_this_run, log)


def decide(item: stage.Item, content_type: str, pdf_bytes: bytes, original, fetched_at: str, state: dict,
           counts: dict, run_id: str, seen_this_run: dict[str, str], log: Callable[[str], None],
           *, reparse: bool = False) -> dict:
    """Validate and stage one fetched PDF (shared by a run and --reparse)."""
    source = item.source
    text, info = stage.pdf_text_info(pdf_bytes)
    h = stage.text_hash(text)
    prev = state.get(item.url)
    row = {"source": source, "title": item.title, "url": item.url, "pdf_url": item.pdf_url, "hash": h,
           "fetched_at": fetched_at, "run_id": run_id, "chars": len(text)}

    def done(outcome: str, **extra) -> dict:
        counts[outcome] += 1
        row.update(outcome=outcome, **extra)
        keep = {k: row[k] for k in ("source", "title", "hash", "fetched_at", "run_id", "outcome", "pdf_url")}
        if outcome == "unchanged":
            keep["run_id"] = prev.get("run_id", run_id)          # staged in that run
            keep["outcome"] = prev["outcome"]
        if item.meta:
            keep["meta"] = item.meta
        state[item.url] = {**keep, **{k: v for k, v in extra.items() if k in ("reason", "doc_id")}}
        log(f"  {outcome:13} {item.title[:70]} ({len(text)} chars)" + (f": {extra['reason']}" if "reason" in extra
                                                                      else ""))
        return row

    if not reparse and prev and prev.get("hash") == h:
        return done("unchanged")
    if content_type == "statute" and stage.core_law(stage.clean_title(item.title)[0]):
        return done("already_held", reason="a core law in the knowledge base")
    if h in seen_this_run:
        reason = f"duplicate (same text as {seen_this_run[h]})"
        stage.quarantine(source, item.url, item.title, reason, text, original, fetched_at)
        return done("quarantined", reason=reason)
    held = None if reparse else _held_by(state, item.url, h, run_id)
    if held:
        return done("already_held", reason=f"same text as {held[0]}")
    seen_this_run[h] = item.url
    try:
        if content_type == "statute":
            recs = stage.statute_records(item, text, info, fetched_at, original)
            stage.write_statute(recs)
            extra = {"doc_id": recs[0]["doc_id"].rsplit("/", 1)[0], "sections": len(recs)}
        else:
            rec = stage.judgment_record(item, text, info, fetched_at, original, stage.sha256(pdf_bytes))
            stage.write_judgment(rec)
            extra = {"doc_id": rec["doc_id"], "paragraphs": len(rec["paragraphs"])}
    except stage.Held as held_core:
        return done("already_held", reason=str(held_core))
    except stage.Quarantine as q:
        stage.quarantine(source, item.url, item.title, str(q), text, original, fetched_at)
        return done("quarantined", reason=str(q))
    if reparse:
        return done(prev.get("outcome") if prev and prev.get("outcome") in ("new", "changed") else "new", **extra)
    return done("changed" if prev else "new", **extra)


def reparse(sources: list[dict], *, log: Callable[[str], None] = print) -> dict:
    """Rebuild every staged record and quarantine entry from the saved
    originals (no network): for parser fixes. Records and quarantine are
    rewritten; state keeps each URL's fetch date. One "reparse" log line."""
    import shutil
    types = {s["name"]: s["content_type"] for s in sources}
    # Listing metadata (category, act number, status) for Pakistan Code URLs, for state entries
    # written before it was stored.
    from app.core.config import settings
    cmap = Path(settings.KB_DIR) / "category_map.json"
    listed = {}
    if cmap.exists():
        listed = {i.url: i.meta for i in pakistan_code_priority(json.loads(cmap.read_text(encoding="utf-8")))}
    state = stage.load_state()
    manifest = {}
    path = stage.scraped_dir() / "originals" / "manifest.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e.get("role") == "pdf":
                for u in (e["url"], e.get("requested_url")):
                    if u:
                        manifest[unquote(u)] = e
    for sub in ("records", "quarantine"):
        shutil.rmtree(stage.scraped_dir() / sub, ignore_errors=True)
    stage.reset_caches()
    run_id = stage.utcnow()
    counts: dict[str, dict] = {}
    seen: dict[str, str] = {}
    for url, e in list(state.items()):
        m = manifest.get(unquote(e.get("pdf_url") or ""))
        source = e.get("source") or (m or {}).get("source")
        c = counts.setdefault(source or "?", dict.fromkeys(COUNTS, 0))
        if not m or source not in types:
            c["errors"] += 1
            continue
        original = Path(m["path"])
        if not original.exists():
            c["errors"] += 1
            continue
        item = stage.Item(source, e.get("title") or "", url, pdf_url=e.get("pdf_url"),
                          meta=e.get("meta") or listed.get(url))
        decide(item, types[source], original.read_bytes(), original, e.get("fetched_at") or run_id, state, c,
               e.get("run_id") or run_id, seen, log, reparse=True)
    stage.save_state(state)
    for source, c in counts.items():
        stage.append_log({"run_at": run_id, "finished_at": stage.utcnow(), "kind": "reparse", "source": source,
                          **{k: c[k] for k in ("new", "changed", "already_held", "quarantined", "errors")}})
    return counts


def listing_pages(src: dict):
    """Listing URLs: listing_urls, then (kb-v2 C8) a paged listing described by
    "paged_listing": {"url": ".../alphabetical/{letter}/{offset}", "letters":
    "ABC...", "step": 10, "max_pages": 60}. Yields (url, letter, offset)."""
    for u in src.get("listing_urls", []):
        yield u, None, None
    paged = src.get("paged_listing")
    if paged:
        for letter in paged.get("letters", ""):
            for n in range(paged.get("max_pages", 60)):
                yield paged["url"].format(letter=letter, offset=n * paged.get("step", 10)), letter, n


def _items(src: dict, fetcher: Fetcher, priority: list, log: Callable[[str], None]):
    """The priority items, then each listing page's items (listing pages are
    fetched only when needed). In a paged listing a letter ends at the first
    page that adds no new item."""
    yield from priority
    seen: set[str] = set()
    done_letter = None
    for listing_url, letter, _offset in listing_pages(src):
        if letter is not None and letter == done_letter:
            continue
        page = fetcher.get(listing_url)
        stage.save_original(src["name"], page.url, page.content, page.content_type, "listing", stage.utcnow())
        found = parse_listing(page.content, page.url, src)
        new = [f for f in found if f.url not in seen]
        log(f"[{src['name']}] {listing_url}: {len(found)} items ({len(new)} new)")
        if letter is not None and not new:
            done_letter = letter
            continue
        for f in new:
            seen.add(f.url)
            yield stage.Item(src["name"], f.title, f.url)


def run(sources: list[dict], fetcher: Fetcher, *, caps: dict[str, int], priority: dict[str, list] | None = None,
        budget: float | None = None, skip_within_hours: float = 20.0, log: Callable[[str], None] = print,
        clock: Callable[[], float] = time.monotonic) -> dict:
    """Stage up to caps[source] documents per source. Returns the summary;
    writes one update-log line per source."""
    t0 = clock()
    run_id = stage.utcnow()
    state = stage.load_state()
    summary: dict = {"run_at": run_id, "complete": True, "per_source": {}, "items": []}
    seen_this_run: dict[str, str] = {}
    spent = False
    for src in sources:
        name = src["name"]
        cap = caps.get(name, 0)
        counts = dict.fromkeys(COUNTS, 0)
        status = "ok"
        if spent:
            status = "not started (time budget spent)"
        else:
            done = 0
            seen_urls: set[str] = set()

            try:
                for item in _items(src, fetcher, (priority or {}).get(name, []), log):
                    if done >= cap:
                        break
                    if item.url in seen_urls:
                        continue
                    seen_urls.add(item.url)
                    done += 1
                    if _recent(state.get(item.url), skip_within_hours):
                        counts["skipped_recent"] += 1
                        continue
                    if budget is not None and clock() - t0 > budget:
                        raise BudgetSpent
                    try:
                        summary["items"].append(process(item, fetcher, src, state, counts, run_id, seen_this_run,
                                                        log))
                    except LimitReachedError:
                        raise
                    except (requests.RequestException, ValueError, RuntimeError, DisallowedError) as e:
                        counts["errors"] += 1
                        summary["items"].append({"source": name, "title": item.title, "url": item.url,
                                                 "outcome": "error", "reason": f"{type(e).__name__}: {str(e)[:160]}"})
                        log(f"  error         {item.title[:70]}: {type(e).__name__}: {str(e)[:120]}")
                    finally:
                        stage.save_state(state)
            except BudgetSpent:
                status, spent = "stopped: time budget spent", True
            except LimitReachedError as e:
                status = f"stopped: {e}"
            except (requests.RequestException, DisallowedError) as e:
                counts["errors"] += 1
                status = f"listing failed: {type(e).__name__}: {str(e)[:120]}"
        if status != "ok":
            summary["complete"] = False
        entry = {"run_at": run_id, "finished_at": stage.utcnow(), "kind": "scrape", "source": name,
                 "content_type": src["content_type"], "cap": cap, **counts, "status": status,
                 "indexed": None}
        stage.append_log(entry)
        summary["per_source"][name] = entry
        log(f"[{name}] {counts} {status}")
    stage.save_state(state)
    return summary


def pakistan_code_priority(cmap: dict) -> list[stage.Item]:
    """The Acts the Pakistan Code category listings name that we don't hold
    (no match, or only a "possible" match, in category_map.json)."""
    out, seen = [], set()
    for c in cmap.get("categories", []):
        for law in c.get("laws", []):
            m = law.get("match")
            if (m is None or m.get("how") == "possible") and law.get("url") and law["url"] not in seen:
                seen.add(law["url"])
                out.append(stage.Item("Pakistan Code", law.get("title") or "", law["url"], meta={
                    "year": law.get("year"), "act_number": law.get("act_number"), "status": law.get("status"),
                    "category": c.get("name")}))
    return out
