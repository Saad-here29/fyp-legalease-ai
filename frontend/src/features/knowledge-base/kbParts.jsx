import { Link } from "react-router-dom";
import { kbRecordPath, shortDate } from "./kbFormat";

// Small pieces shared by the Knowledge Base page, Research results and AI
// Chat sources. Tags always pair colour with words (STYLE_GUIDE §04).

export function TierTag({ tier }) {
  if (tier == null) return null;
  return (
    <span
      className={`${tier === 1 ? "ds-tag-active" : "ds-tag-neutral"} whitespace-nowrap`}
      title={tier === 1 ? "Tier 1: matched a Pakistan Code listing" : `Tier ${tier}: not matched to a Pakistan Code listing`}
    >
      Tier {tier}
    </span>
  );
}

const STATUS = {
  current: null,
  under_review: { cls: "ds-tag-review", label: "! Under review" },
  repealed: { cls: "ds-tag-neutral", label: "Repealed" },
};

export function KbStatusTag({ status }) {
  const s = STATUS[status];
  return s ? <span className={`${s.cls} whitespace-nowrap`}>{s.label}</span> : null;
}

// Fetched from an official website by the scraper (kb-v2 C3).
export function ScrapedTag({ scraped, fetchedAt }) {
  if (!scraped) return null;
  return (
    <span
      className="ds-tag-active whitespace-nowrap"
      title={`Scraped from the source website${fetchedAt ? ` on ${shortDate(fetchedAt)}` : ""}; staged, not yet reviewed`}
    >
      Scraped
    </span>
  );
}

export function KbSourceLink({ sourceUrl, recordId, className = "ds-link text-[15px]" }) {
  if (sourceUrl) {
    return (
      <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className={className}>
        Source
      </a>
    );
  }
  const to = kbRecordPath(recordId);
  return to ? (
    <Link to={to} className={className}>
      Record in Knowledge Base
    </Link>
  ) : null;
}
