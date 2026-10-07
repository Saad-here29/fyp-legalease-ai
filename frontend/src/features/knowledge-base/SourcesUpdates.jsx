import { shortDate } from "./kbFormat";

// Knowledge Base "Sources and updates" (kb-v2 C3): the scraping update log
// (storage/kb/scraped/update_log.jsonl via /kb/updates). Shown only when
// SCRAPED_V2 is on (the endpoint is a 404 otherwise).

const time = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

const COLS = [
  ["fetched", "Fetched"],
  ["new", "New"],
  ["changed", "Changed"],
  ["unchanged", "Unchanged"],
  ["already_held", "Already held"],
  ["quarantined", "Quarantined"],
  ["indexed", "Searchable"],
];

export default function SourcesUpdates({ updates }) {
  const scrapes = updates.entries.filter((e) => e.kind === "scrape").slice(0, 12);
  const lastIndex = updates.entries.find((e) => e.kind === "index");
  const reasons = Object.entries(updates.quarantine || {});
  return (
    <section className="mt-12" aria-labelledby="updates-heading">
      <div className="flex flex-wrap items-end justify-between gap-4 pb-3 border-b-2 border-ds-ink">
        <h2 id="updates-heading" className="ds-h2">
          Sources and updates
        </h2>
        <p className="ds-meta">
          {lastIndex
            ? `Embedded ${time(lastIndex.run_at)}${lastIndex.complete ? "" : " (partly: next run continues)"}`
            : "Not embedded yet"}
        </p>
      </div>
      <p className="ds-body text-ds-text-2 mt-4 max-w-[760px]">
        Pakistan Code, Khyber Pakhtunkhwa Code and Federal Shariat Court are checked by the scraper (identified,
        2 seconds between requests, robots.txt respected). Every page and PDF is saved unchanged with its source URL,
        date and SHA-256. Documents that fail validation are quarantined and never searched.
      </p>
      {scrapes.length === 0 ? (
        <p className="ds-body text-ds-text-2 py-6">No scraping run yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left mt-4 min-w-[720px]">
            <thead>
              <tr className="border-b border-ds-rule">
                <th scope="col" className="ds-meta py-3 pr-4">Run</th>
                <th scope="col" className="ds-meta py-3 pr-4">Source</th>
                {COLS.map(([, h]) => (
                  <th key={h} scope="col" className="ds-meta py-3 pr-4 text-right">
                    {h}
                  </th>
                ))}
                <th scope="col" className="ds-meta py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {scrapes.map((e) => (
                <tr key={`${e.run_at}-${e.source}`} className="border-b border-ds-rule align-top">
                  <td className="py-3 pr-4 ds-body text-ds-text-2 whitespace-nowrap">{time(e.run_at)}</td>
                  <td className="py-3 pr-4 ds-body">{e.source}</td>
                  {COLS.map(([k]) => (
                    <td key={k} className="py-3 pr-4 ds-body text-right tabular-nums">
                      {k === "indexed" && e[k] == null ? <span className="text-ds-text-2">pending</span> : e[k]}
                    </td>
                  ))}
                  <td className="py-3 ds-body text-ds-text-2">{e.status === "ok" ? "OK" : e.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {reasons.length > 0 && (
        <p className="ds-body text-ds-text-2 mt-4">
          Quarantined, by reason: {reasons.map(([r, n]) => `${r} (${n})`).join(" · ")}
        </p>
      )}
      {scrapes[0] && <p className="ds-meta mt-2">Last checked {shortDate(scrapes[0].finished_at || scrapes[0].run_at)}</p>}
    </section>
  );
}
