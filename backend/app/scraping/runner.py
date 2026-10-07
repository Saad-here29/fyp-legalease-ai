"""One scraping run over the configured sources, with change detection.

For each built source: listing pages -> items -> (document page ->) PDF -> text
-> hash, then compared with the latest stored version of that URL:
  no stored version, title already in the corpus  -> "baseline" (status
      approved: we already have it; not reported as new)
  no stored version otherwise                     -> "new", staged
  stored, same hash                               -> unchanged
  stored, different hash                          -> "changed": new version,
      staged; the previous version is kept (is_latest = false)
Every outcome is counted per source in the run summary, and listed per
document in summary["items"] (source, title, URL, hash, outcome). --dry-run
fetches and compares but writes nothing; without a database it compares with
`previous` (URL -> hash from an earlier run's summary), so change detection
can be shown with no tables at all.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from types import SimpleNamespace

import requests
from sqlalchemy.orm import Session

from app.models.scraping import ScrapedDocument, ScrapeRun
from app.scraping.fetcher import DisallowedError, Fetcher, LimitReachedError
from app.scraping.parse import content_hash, find_pdf_url, normalise_title, parse_listing, pdf_text


def now() -> datetime:
    return datetime.now(UTC)


def load_corpus_titles(records: Iterable[dict]) -> set[str]:
    return {normalise_title(r.get("title") or r.get("source") or "") for r in records} - {""}


def _latest(db: Session | None, url: str) -> ScrapedDocument | None:
    if db is None:
        return None
    return (db.query(ScrapedDocument)
            .filter(ScrapedDocument.source_url == url, ScrapedDocument.is_latest.is_(True))
            .one_or_none())


def classify(previous: ScrapedDocument | None, new_hash: str, title: str, content_type: str,
             corpus_titles: set[str]) -> str:
    """'baseline', 'new', 'changed' or 'unchanged'."""
    if previous is None:
        if content_type == "statute" and normalise_title(title) in corpus_titles:
            return "baseline"
        return "new"
    return "unchanged" if previous.content_hash == new_hash else "changed"


def run(sources: list[dict], fetcher: Fetcher, *, db: Session | None, corpus_titles: set[str],
        limit: int | None = None, dry_run: bool = False, log=print,
        previous: dict[str, str] | None = None) -> dict:
    built = [s for s in sources if s.get("enabled")]
    per_item_quota = math.ceil(limit / len(built)) if limit and built else None
    run_row = ScrapeRun(id=uuid.uuid4(), started_at=now(), dry_run=dry_run)
    summary: dict[str, dict] = {}
    items_out: list[dict] = []
    stop = False
    for src in built:
        counts = {"checked": 0, "new": 0, "changed": 0, "unchanged": 0, "baseline": 0, "errors": 0,
                  "content_type": src["content_type"], "status": "ok", "error_samples": []}
        summary[src["name"]] = counts
        if stop:
            counts["status"] = "skipped (run cap reached)"
            continue
        done = 0
        try:
            for listing_url in src["listing_urls"]:
                page = fetcher.get(listing_url)
                items = parse_listing(page.content, page.url, src)
                log(f"[{src['name']}] {listing_url}: {len(items)} items")
                for item in items:
                    if per_item_quota is not None and done >= per_item_quota:
                        break
                    done += 1
                    counts["checked"] += 1
                    try:
                        if src.get("item_is_pdf"):
                            pdf_url = item.url
                        else:
                            doc_page = fetcher.get(item.url)
                            pdf_url = find_pdf_url(doc_page.content, doc_page.url, src)
                            if not pdf_url:
                                raise ValueError("no PDF link on the document page")
                        pdf = fetcher.get(pdf_url, pdf=True)
                        if "pdf" not in pdf.content_type.lower() and not pdf.content[:4] == b"%PDF":
                            raise ValueError(f"not a PDF ({pdf.content_type})")
                        text = pdf_text(pdf.content)
                        h = content_hash(text)
                        prev = _latest(db, item.url)
                        if prev is None and db is None and previous and item.url in previous:
                            prev = SimpleNamespace(content_hash=previous[item.url])   # an earlier dry run
                        kind = classify(prev, h, item.title, src["content_type"], corpus_titles)
                        counts[kind] += 1
                        items_out.append({"source": src["name"], "title": item.title, "url": item.url,
                                          "pdf_url": pdf_url, "content_hash": h, "outcome": kind,
                                          "chars": len(text)})
                        log(f"  {kind:9} {item.title[:70]} ({len(text)} chars)")
                        if dry_run or db is None or kind == "unchanged":
                            continue
                        if prev is not None:
                            prev.is_latest = False
                        db.add(ScrapedDocument(
                            source_name=src["name"], source_url=item.url, pdf_url=pdf_url,
                            title=item.title[:500], content_type=src["content_type"], content_hash=h,
                            text=text, fetched_at=now(),
                            first_seen_at=prev.first_seen_at if prev else now(),
                            status="approved" if kind == "baseline" else "staged",
                            change_kind=kind, in_corpus=kind == "baseline",
                            version=(prev.version + 1) if prev else 1, is_latest=True, run_id=run_row.id))
                    except LimitReachedError:
                        counts["checked"] -= 1   # the cap stopped it before it was checked
                        raise
                    except (requests.RequestException, ValueError, RuntimeError, DisallowedError) as e:
                        counts["errors"] += 1
                        items_out.append({"source": src["name"], "title": item.title, "url": item.url,
                                          "pdf_url": None, "content_hash": None, "outcome": "error",
                                          "error": f"{type(e).__name__}: {str(e)[:120]}"})
                        if len(counts["error_samples"]) < 3:
                            counts["error_samples"].append(f"{item.url}: {type(e).__name__}: {str(e)[:120]}")
                        log(f"  ERROR {item.url}: {e}")
                if per_item_quota is not None and done >= per_item_quota:
                    break
        except LimitReachedError as e:
            counts["status"] = f"stopped: {e}"
            stop = True
        except (requests.RequestException, DisallowedError) as e:
            counts["errors"] += 1
            counts["status"] = f"listing failed: {type(e).__name__}"
            counts["error_samples"].append(str(e)[:160])
    run_row.finished_at = now()
    run_row.pages_checked = fetcher.pages
    run_row.new_count = sum(c["new"] for c in summary.values())
    run_row.changed_count = sum(c["changed"] for c in summary.values())
    run_row.error_count = sum(c["errors"] for c in summary.values())
    run_row.per_source = summary
    if db is not None and not dry_run:
        db.add(run_row)
        db.commit()
    return {"started_at": run_row.started_at.isoformat(), "finished_at": run_row.finished_at.isoformat(),
            "pages_checked": fetcher.pages, "requests": fetcher.requests_made, "pdfs": fetcher.pdfs,
            "new": run_row.new_count, "changed": run_row.changed_count, "errors": run_row.error_count,
            "dry_run": dry_run, "per_source": summary, "items": items_out}
