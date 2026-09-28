import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Check, Menu, X } from "lucide-react";
import Wordmark from "@/components/common/Wordmark";
import { ArchOutlines } from "@/components/common/ArchPattern";
import { ROUTES } from "@/constants";
import { researchApi } from "@/features/legal-research/api";

// Public landing page — design system v1, per docs/design_reference page 3.
// Every claim must match the product as built: the library is federal
// Pakistani statute text only (no judgments, no jurisdiction/court/year
// filters); extracted document values carry no page numbers; there is no
// calendar, cause list, messaging, moot folder, practice simulator, pricing
// or trial. The examples in the illustrations are real outputs seen in the
// app (Sept 2026): Cr.P.C. s. 497 as a search result, the MFLO s. 7 talaq
// answer, the NER output for Crl.P. 187-P/2026, an NDA compliance check.

const GUTTER = "px-6 sm:px-10 lg:px-24";
const COLUMN = "max-w-[1240px] mx-auto";

const NAV = [
  ["Research", "#research"],
  ["AI Chat", "#chat"],
  ["Documents", "#documents"],
  ["Contracts", "#contracts"],
];

export default function LandingPage() {
  const { data: stats } = useQuery({ queryKey: ["research-stats"], queryFn: researchApi.stats, staleTime: Infinity });
  const statutes = stats?.documents ? stats.documents.toLocaleString() : "900";

  return (
    <div className="min-h-screen bg-ds-paper font-ds-sans text-ds-text">
      <Hero />
      <Promises statutes={statutes} />
      <Modules />
      <Seats />
      <Closing />
      <footer className={`${GUTTER} border-t border-ds-rule`}>
        <div className={`${COLUMN} py-8 flex flex-wrap items-center justify-between gap-4 ds-meta`}>
          <span>© 2026 LegalEase AI</span>
          <span>LegalEase AI assists legal work; it does not replace advice from a qualified advocate.</span>
        </div>
      </footer>
    </div>
  );
}

function Nav() {
  const [open, setOpen] = useState(false);
  const link =
    "font-ds-sans text-[15px] text-ds-paper/80 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-ds-paper rounded-ds-sm";
  return (
    <nav className={`${COLUMN} flex items-center justify-between h-20`} aria-label="Main">
      <Link to={ROUTES.LANDING} aria-label="LegalEase AI home" className="rounded-ds">
        <Wordmark onInk />
      </Link>
      <div className="hidden md:flex items-center gap-8">
        {NAV.map(([label, href]) => (
          <a key={href} href={href} className={link}>
            {label}
          </a>
        ))}
      </div>
      <Link to={ROUTES.LOGIN} className="hidden md:inline-flex ds-btn-secondary-on-ink">
        Sign in
      </Link>
      <button
        className="md:hidden h-11 w-11 flex items-center justify-center text-ds-paper"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close menu" : "Open menu"}
        aria-expanded={open}
      >
        {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>
      {open && (
        <div className="md:hidden absolute top-20 inset-x-0 z-20 bg-ds-ink border-t border-ds-paper/15 px-6 py-4 flex flex-col">
          {NAV.map(([label, href]) => (
            <a key={href} href={href} onClick={() => setOpen(false)} className={`${link} py-3`}>
              {label}
            </a>
          ))}
          <Link to={ROUTES.LOGIN} className="ds-btn-secondary-on-ink mt-3">
            Sign in
          </Link>
        </div>
      )}
    </nav>
  );
}

function Hero() {
  return (
    <header className={`relative bg-ds-ink text-ds-paper overflow-hidden ${GUTTER}`}>
      <ArchOutlines className="text-ds-paper/[0.06]" />
      <div className="relative">
        <Nav />
        <div className={`${COLUMN} grid gap-14 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] items-center pt-12 pb-20 lg:pt-16 lg:pb-24`}>
          <div>
            <p className="font-ds-sans font-semibold text-[13px] uppercase tracking-[0.16em] text-ds-paper/70">
              For advocates, clients and law students in Pakistan
            </p>
            <h1 className="mt-6 font-ds-serif font-medium text-[44px] leading-[48px] sm:text-[60px] sm:leading-[64px] xl:text-[72px] xl:leading-[76px] tracking-tight text-ds-paper">
              Pakistani law, researched in minutes.{" "}
              <em className="font-normal italic text-[#EBC7B8]">Cited to the source.</em>
            </h1>
            <p className="mt-8 max-w-[560px] text-[18px] leading-[30px] text-ds-paper/80">
              LegalEase AI searches Pakistani statute text, analyses the documents in your file, drafts contracts against a
              compliance checklist — and keeps every case in one place.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-6">
              {/* Sign-up starts at the Welcome role choice, which leads to the form. */}
              <Link to={ROUTES.WELCOME} className="ds-btn-primary px-8">
                Create an account
              </Link>
              <a
                href="#promises"
                className="font-ds-sans font-semibold text-[16px] text-ds-paper underline decoration-ds-paper/40 decoration-2 underline-offset-[5px] hover:decoration-ds-paper"
              >
                See how answers are checked
              </a>
            </div>
            <p className="mt-12 pt-5 border-t border-ds-paper/15 flex items-start gap-3 text-[15px] leading-[24px] text-ds-paper/80 max-w-[560px]">
              <Check className="h-5 w-5 shrink-0 mt-0.5 text-[#8FC7A4]" strokeWidth={2.5} aria-hidden="true" />
              <span>
                <strong className="text-white font-semibold">No invented case law.</strong> Case citations the library
                can&apos;t show are removed, and section references are checked against the statute text.
              </span>
            </p>
          </div>
          <HeroAnswer />
        </div>
      </div>
    </header>
  );
}

// A real answer from the app (MFLO s. 7, talaq), shown in the chat's format.
function HeroAnswer() {
  return (
    <div className="relative bg-ds-sheet text-ds-text rounded-ds p-7 shadow-none max-w-[520px] lg:ml-auto w-full">
      <span className="absolute -top-3.5 right-6 rotate-[3deg] border-2 border-ds-pass text-ds-pass bg-ds-sheet px-2.5 py-1 font-ds-sans font-semibold text-[12px] uppercase tracking-[0.12em] rounded-ds-sm">
        Checked against source
      </span>
      <p className="ds-eyebrow mb-3">Example</p>
      <p className="ds-meta">You asked</p>
      <p className="font-ds-sans font-semibold text-[17px] leading-[24px] mt-1">
        What is the procedure for talaq under Section 7?
      </p>
      <div className="mt-5 pt-5 border-t-2 border-ds-ink">
        <p className="font-ds-sans font-semibold text-[15px] text-ds-text-2">Short answer</p>
        <p className="font-ds-sans text-[16px] leading-[26px] mt-1">
          The husband must give written notice to the Chairman, who forms an Arbitration Council within 30 days; the talaq
          takes effect only after 90 days.<Cite n="1" />
        </p>
        <p className="ds-meta mt-4 flex flex-wrap items-center gap-x-2">
          1 statute · 7.2s ·
          <span className="inline-flex items-center gap-1 font-semibold text-ds-pass">
            <Check className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" /> Checked against source
          </span>
        </p>
        <p className="mt-4 pt-3 border-t border-ds-rule font-ds-sans text-[14px]">
          <span className="font-semibold">[1]</span> Muslim Family Laws Ordinance, 1961 — Section 7
        </p>
      </div>
    </div>
  );
}

function Cite({ n }) {
  return (
    <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1 mx-1 rounded-ds-sm bg-ds-ink text-white text-[12px] font-semibold align-[0.12em]">
      {n}
    </span>
  );
}

function Promises({ statutes }) {
  const items = [
    [
      "Sources, not guesses.",
      "Every answer cites the statute passages it relies on. If the library doesn't cover a question, LegalEase says so instead of inventing an answer.",
    ],
    [
      "Pakistani law first.",
      `About ${statutes} Pakistani legal documents — mostly Acts, Ordinances, Codes and Orders — searched by meaning. Questions outside Pakistani law are refused.`,
    ],
    [
      "Your files stay yours.",
      "A case, and the documents on it, are visible only to its lawyer and the client they link. Documents you upload on your own stay visible to you alone.",
    ],
  ];
  return (
    <section id="promises" className={`${GUTTER} py-24`}>
      <div className={COLUMN}>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.7fr)] items-end">
          <h2 className="ds-h1">Three promises we hold every answer to.</h2>
          <p className="ds-body text-ds-text-2 text-[17px]">
            Legal work can&apos;t run on guesses. These are the rules the product is built around.
          </p>
        </div>
        <div className="mt-14 grid gap-10 md:grid-cols-3">
          {items.map(([title, body], i) => (
            <div key={title} className="ds-section">
              <p className="font-ds-serif italic text-[20px] text-ds-text-2">{["i.", "ii.", "iii."][i]}</p>
              <h3 className="ds-h3 mt-2">{title}</h3>
              <p className="ds-body text-ds-text-2 mt-3">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Modules() {
  const rows = [
    {
      id: "research",
      title: "Legal research",
      body: "Search Pakistani statute text in plain language. Results are the passages closest in meaning to your query, and each opens in full — with an AI breakdown on request.",
      note: "Results come from the text of the law — not from a summary of it.",
      visual: (
        <>
          <div className="ds-input flex items-center text-[15px] text-ds-text">bail in a non-bailable offence</div>
          <Result kind="Statute" title="Code of Criminal Procedure, 1898 — s. 497" />
          <Result kind="Statute" title="When bail may be taken in case of non-bailable offence" meta />
        </>
      ),
    },
    {
      id: "chat",
      title: "AI chat, with footnotes",
      body: "Ask a question the way you'd ask a senior, in English or Urdu. Answers open with a short answer, then the detail, with numbered citations underneath.",
      note: "Section references are checked against the retrieved statute text.",
      visual: (
        <>
          <p className="font-ds-sans font-semibold text-[15px]">Short answer</p>
          <p className="font-ds-sans text-[15px] leading-[24px] mt-1">
            A talaq takes effect 90 days after notice to the Chairman.<Cite n="1" />
          </p>
          <p className="ds-meta mt-3 flex items-center gap-2">
            1 statute ·
            <span className="inline-flex items-center gap-1 font-semibold text-ds-pass">
              <Check className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" /> Checked against source
            </span>
          </p>
        </>
      ),
    },
    {
      id: "documents",
      title: "Document analysis",
      body: "Upload a judgment, agreement or plaint. Get a plain-language summary and, separately, the parties, dates and references pulled out for you to check.",
      note: "Parties, dates and references come from an entity model trained on Pakistani judgments.",
      visual: (
        <dl className="font-ds-sans text-[14px]">
          {[
            ["Party", "Nadar Khan"],
            ["Date", "21.09.2026"],
            ["Reference", "Criminal Petition No.187-P of 2026"],
          ].map(([k, v]) => (
            <div key={k} className="grid grid-cols-[100px_1fr] gap-3 py-2.5 border-b border-ds-rule last:border-0">
              <dt className="text-ds-text-2">{k}</dt>
              <dd className="font-semibold">{v}</dd>
            </div>
          ))}
        </dl>
      ),
    },
    {
      id: "contracts",
      title: "Contract drafting",
      body: "Start from an NDA, employment or service agreement template, fill in the facts, and a compliance checklist marks each clause the template requires as found or missing.",
      note: "A keyword check you can repeat on every version — not another AI call.",
      visual: (
        <ul className="font-ds-sans text-[14px]">
          <li className="flex items-center justify-between gap-3 py-2.5 border-b border-ds-rule">
            Confidentiality clause <span className="ds-tag-pass h-7 text-[13px]">Passes</span>
          </li>
          <li className="flex items-center justify-between gap-3 py-2.5">
            Governing law clause <span className="ds-tag-fail h-7 text-[13px]">Fails</span>
          </li>
        </ul>
      ),
    },
  ];

  return (
    <section className={`${GUTTER} pb-24`}>
      <div className={`${COLUMN} border-t-2 border-ds-ink`}>
        {rows.map((r, i) => (
          <div
            key={r.id}
            id={r.id}
            className="scroll-mt-6 grid gap-8 lg:grid-cols-[110px_minmax(0,1fr)_minmax(0,0.85fr)] py-12 border-b border-ds-rule"
          >
            <p className="font-ds-serif text-[56px] leading-none text-ds-text-2">{String(i + 1).padStart(2, "0")}</p>
            <div>
              <h3 className="ds-h2">{r.title}</h3>
              <p className="ds-body text-ds-text-2 mt-3 text-[17px] leading-[28px] max-w-[520px]">{r.body}</p>
              <p className="mt-4 flex items-start gap-2 font-ds-serif italic text-[16px] text-ds-pass max-w-[520px]">
                <Check className="h-4 w-4 shrink-0 mt-1" strokeWidth={2.5} aria-hidden="true" />
                {r.note}
              </p>
            </div>
            <div className="bg-ds-sheet border border-ds-rule rounded-ds p-6 self-start">
              {/* Illustrations reproduce real app output but are static, so they're labelled. */}
              <p className="ds-eyebrow mb-3">Example</p>
              {r.visual}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Result({ kind, title, meta = false }) {
  return (
    <div className={meta ? "pt-1" : "mt-5 pt-4 border-t border-ds-rule"}>
      {!meta && <p className="font-ds-sans font-semibold text-[12px] uppercase tracking-[0.12em] text-ds-text-2">{kind}</p>}
      <p className={meta ? "ds-meta" : "font-ds-sans font-semibold text-[15px] mt-1"}>{title}</p>
    </div>
  );
}

function Seats() {
  const seats = [
    ["Advocates", "Cases, research, document analysis and contract drafts in one place. Link a client to a case and they can follow its progress."],
    ["Clients", "See where your case stands and what each stage means, in plain language. Ask the AI about Pakistani law."],
    ["Law students", "Ask about statutes and concepts and get answers that cite the text, and search the statute library by meaning."],
  ];
  return (
    <section className={`bg-ds-ink text-ds-paper ${GUTTER} py-24`}>
      <div className={COLUMN}>
        <h2 className="font-ds-serif font-medium text-[36px] leading-[44px] lg:text-[48px] lg:leading-[56px] tracking-tight">
          One platform, three seats at the table.
        </h2>
        <div className="mt-12 grid gap-10 md:grid-cols-3">
          {seats.map(([title, body]) => (
            <div key={title} className="pt-6 border-t border-ds-paper/20">
              <h3 className="font-ds-sans font-semibold text-[22px] leading-[30px] text-white">{title}</h3>
              <p className="mt-3 text-[16px] leading-[26px] text-ds-paper/75">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Closing() {
  return (
    <section className={`${GUTTER} py-24 text-center`}>
      <div className={COLUMN}>
        <h2 className="ds-h1 max-w-[720px] mx-auto">Bring your next brief to LegalEase.</h2>
        <p className="ds-body text-ds-text-2 text-[17px] mt-5">Sign up as a lawyer, client or law student.</p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
          <Link to={ROUTES.WELCOME} className="ds-btn-primary px-8">
            Create an account
          </Link>
        </div>
        <p className="ds-body text-ds-text-2 mt-6">
          Already have an account?{" "}
          <Link to={ROUTES.LOGIN} className="ds-link-seal">
            Sign in
          </Link>
        </p>
      </div>
    </section>
  );
}
