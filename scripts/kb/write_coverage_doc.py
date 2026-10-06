"""Write docs/kb_coverage_2026-10-06.md from backend/storage/kb/category_map.json (offline)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
m = json.loads((ROOT / "backend/storage/kb/category_map.json").read_text(encoding="utf-8"))
cats = m["categories"]
USER = {"Criminal Laws": 69, "Civil Laws": 147, "Family Laws": 22, "Service Laws": 25, "Labour Laws": 41,
        "Police Laws": 4, "Companies Laws": 9, "Land/Property Laws": 18, "Islamic/Religious Laws": 5,
        "Banking/Financial Laws": 27, "Law of Evidence": 1, "Rent Laws": 3, "International Laws": 7,
        "Land Reform Laws": 2, "Excise/Taxation Laws": 14, "Military Laws": 18, "Health/Medical Laws": 18,
        "Media Laws": 3, "Election Laws": 8, "Departmental Laws": 126, "General Laws": 135}


def esc(s):
    return (s or "").replace("|", "\\|")


L = []
L.append("""# Knowledge base v2: Pakistan Code coverage (2026-10-06)

This compares the Pakistan Code's category listings with the statutes in
our corpus (`docs/corpus_statute_list.md`: 900 titles). The source data is
`backend/storage/kb/category_map.json`, built by
`scripts/kb/build_category_map.py`.

**What was fetched:** only the category index and the 23 category listing
pages, on 2026-10-06, with the scraper's polite rules. That was 25 requests
in total, including robots.txt, 2 s apart, with the User-Agent
`LegalEase-FYP/0.1 (… contact: i228795@nu.edu.pk)`. robots.txt allowed it
and nothing was refused. No law pages or PDFs were downloaded.

## What could and couldn't be verified

- **Verified: your 21 category counts.** They match the badge counts the
  site shows next to each category, all 21 exactly. They total **702**.
  Tenancy Laws and Minorities Laws show 0.
- **Verified: what each category page actually lists.** That's **526
  Acts** in total, all distinct (no Act is in two categories).
- **Not verified: the other 176.** Every category lists fewer Acts than its
  badge (e.g. Criminal 69 vs 44). The pages have no pagination and no second
  section: the "secondary legislation" tab is empty. The badges probably also
  count inactive, repealed or subordinate entries that aren't listed. I
  didn't guess at other URLs to find them.
- **Matching:** titles were compared after removing:
  - status notes such as "(Repealed by …)" and "(Under Review)", which are
    kept separately as `status`;
  - abbreviations such as "(CPC)";
  - page boilerplate such as "UNDER PROOF READING Page 1 of 24";
  - the year, case, spacing and punctuation.

  The year then has to agree when both sides have one. The match levels:
  - **exact:** the cleaned titles are equal;
  - **near:** a 93% or better spelling match, mostly OCR damage. Counted as
    held, and listed below for review;
  - **possible:** 85% or better. **Not** counted as held (it may be a
    different or renamed Act). Listed below.
- **Not verified: that a matched Act's text is the current version.**
  Matching is by title and year only. Comparing text needs the Act's PDF,
  which is out of Phase A.

## Per category

| Category | Your count | Site badge | Listed on the page | We hold | Possible match | Missing (of listed) | Listed as repealed / under review |
|---|---:|---:|---:|---:|---:|---:|---|
""")
for c in cats:
    if c["name"] in ("Tenancy Laws", "Minorities Laws") and not c["listed_count"]:
        continue
    sc = c["status_counts"]
    L.append(f"| {c['name']} | {USER.get(c['name'], '–')} | {c['badge_count']} | {c['listed_count']} | {c['held']} | "
             f"{c['possible']} | {c['missing']} | {sc['repealed']} / {sc['under_review']} |\n")
tl = sum(c["listed_count"] for c in cats)
th = sum(c["held"] for c in cats)
tp = sum(c["possible"] for c in cats)
L.append(f"| **Total** | **{sum(USER.values())}** | **{sum(c['badge_count'] or 0 for c in cats)}** | **{tl}** | **{th}** | "
         f"**{tp}** | **{tl - th}** | |\n")
L.append(f"\n**We hold {th} of the {tl} listed Acts ({th * 100 / tl:.0f}%).** "
         f"{tp} more are possible matches that need checking. Tenancy Laws and Minorities Laws list 0 and are left out.\n")

L.append("\n## Missing titles: Family, Criminal, Civil, Law of Evidence\n\n"
         "Every listed Act we don't hold, with possible matches marked.\n")
for name in ("Family Laws", "Criminal Laws", "Civil Laws", "Law of Evidence"):
    c = next(x for x in cats if x["name"] == name)
    miss = [law for law in c["laws"] if not law["match"] or law["match"]["how"] == "possible"]
    L.append(f"\n### {name}: {len(miss)} of {c['listed_count']} listed\n\n")
    if not miss:
        L.append("None: we hold every listed Act.\n")
    for law in miss:
        note = f" (possible match: \"{law['match']['corpus'][0]['title']}\"; check whether it's the same Act)" if law["match"] else ""
        st = "" if law["status"] == "current" else f" ({law['status'].replace('_', ' ')})"
        L.append(f"- {law['clean_title']}, {law['act_number'] or 'no act number listed'}{st}{note}\n")

near = [(c["name"], law) for c in cats for law in c["laws"] if law["match"] and law["match"]["how"] == "near"]
L.append(f"\n## Near matches counted as held ({len(near)}; check them once)\n\n"
         "| Category | Pakistan Code title | Our title |\n|---|---|---|\n")
for cname, law in near:
    L.append(f"| {cname} | {esc(law['clean_title'])} | {esc(law['match']['corpus'][0]['title'])} |\n")

L.append("""
## Notable findings

- **The Muslim Family Laws Ordinance, 1961 isn't in any category listing,**
  though it's on the site and in our corpus. The "Family Laws" page lists 19
  Acts, without the MFLO or the West Pakistan Family Courts Act. So the
  category map can't be the only list of what to fetch: the alphabetical
  index is also needed (a later phase).
- **The site's own metadata disagrees in places.** For example, "Dowry and
  Bridal Gifts (Restriction) Act, 1976" is listed with act number "XLIII of
  1974" and date June 4 1974. Records take the year from the title and keep
  the listed act number as is.
- **Some listed titles carry status notes,** e.g. "Code of Civil Procedure
  (CPC), 1908 (Under Review)" and "(Repealed by Act XIV of 2015)". These
  become the record's `status`. Repealed Acts we don't hold aren't urgent.
""")

un = m["corpus_unmatched"]
by = defaultdict(list)
for u in un:
    by[u["reason"]].append(u)
L.append(f"\n## Our documents that matched no listed Pakistan Code title ({len(un)} of {m['corpus_titles']})\n\n"
         "They're grouped by a simple title rule, so treat the groups as a guide, not a verdict:\n\n")
for reason, n in Counter(u["reason"] for u in un).most_common():
    L.append(f"- **{reason}:** {n}\n")
L.append("""
**Why most don't match:** the category pages list only 526 Acts, while our
corpus has 893 titles extracted from Pakistan Code PDFs. So most of them are
probably federal Acts that the site simply doesn't place in a category. That
can be confirmed against the alphabetical index in the next phase; it isn't
verified here.
""")
for reason in ("provincial or pre-1955 regional law", "rules / regulations / orders / manual",
               "duplicate spelling of another corpus title", "boilerplate title (extraction failed)",
               "federal title not in any category listing (or a spelling we couldn't match)"):
    items = by.get(reason, [])
    if not items:
        continue
    L.append(f"\n### {reason[0].upper() + reason[1:]} ({len(items)})\n\n")
    for u in sorted(items, key=lambda x: x["title"].lower()):
        L.append(f"- {u['title']} ({u['chunks']} chunks)\n")

out = ROOT / "docs" / "kb_coverage_2026-10-06.md"
out.write_text("".join(L), encoding="utf-8")
print("written", out, len("".join(L)))
