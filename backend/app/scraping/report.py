"""Human-readable end-of-run summary for scripts/scraping/scrape_laws.py (kb-v2 B8).

One row per document checked: source, URL, outcome, the first 8 characters
of its content hash, and what a real run would do with it. Nothing the
scraper fetches is searchable: new and changed documents are staged for
review, and only an approved, re-built index makes text searchable.
"""

from __future__ import annotations

# What a real (non-dry) run would do with each outcome.
WOULD_STAGE = {"new": "yes", "changed": "yes (new version; old kept)", "unchanged": "no (same hash)",
               "baseline": "no (already in corpus)", "error": "no (fetch failed)"}


def previous_hashes(summary: dict) -> dict[str, str]:
    """URL -> content hash from an earlier run's --out JSON."""
    return {i["url"]: i["content_hash"] for i in summary.get("items", []) if i.get("content_hash")}


def render(summary: dict, *, max_url: int = 60) -> str:
    items = summary.get("items", [])
    rows = [("Source", "URL", "Status", "Hash", "Would stage", "Indexed")]
    for i in items:
        url = i["url"] if len(i["url"]) <= max_url else i["url"][: max_url - 1] + "…"
        rows.append((i["source"], url, i["outcome"], (i.get("content_hash") or "-")[:8],
                     WOULD_STAGE.get(i["outcome"], "no"), "no"))
    widths = [max(len(r[c]) for r in rows) for c in range(len(rows[0]))]
    line = "  ".join("-" * w for w in widths)
    out = ["", "Summary" + (" (dry run: nothing was written)" if summary.get("dry_run") else ""), line]
    for n, r in enumerate(rows):
        out.append("  ".join(cell.ljust(w) for cell, w in zip(r, widths, strict=True)).rstrip())
        if n == 0:
            out.append(line)
    out.append(line)
    counts = {k: sum(1 for i in items if i["outcome"] == k) for k in ("new", "changed", "unchanged", "baseline", "error")}
    out.append(f"{len(items)} documents: {counts['new']} new, {counts['changed']} changed, {counts['unchanged']} "
               f"unchanged, {counts['baseline']} already in the corpus, {counts['error']} failed. "
               f"{summary.get('requests', 0)} requests. Indexed: none (staged documents wait for review).")
    return "\n".join(out)
