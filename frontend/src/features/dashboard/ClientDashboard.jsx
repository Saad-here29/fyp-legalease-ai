import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import StatusTag from "@/features/case-management/StatusTag";
import { STATUS, TYPE_LABEL, fmtDate, readableTimelineEntry, isUpcoming } from "@/features/case-management/caseMeta";
import { RuledSection, ViewAll, Today } from "./components/DashParts";

// Client dashboard — design system v1, per docs/design_reference page 5.
// Adapted to what exists: no messages or requested-document checklist (not
// built); the next hearing date is shown when the lawyer has set one. "Where your case stands" follows the case's
// real status; the stage notes below are fixed text, not AI output.

const STAGES = ["created", "assigned", "in_progress", "hearing_scheduled", "closed"];

const STAGE_NOTE = {
  created: "Your lawyer has opened this case in LegalEase. Nothing is needed from you yet.",
  assigned: "Your lawyer is assigned to the case and preparing it. They may ask you for documents.",
  in_progress:
    "Your lawyer is working on the case — preparing and filing papers and dealing with the other side. They will contact you if they need anything from you.",
  hearing_scheduled:
    "The case has reached the hearing stage. Your lawyer will tell you the date and whether you need to attend.",
  closed: "Your lawyer has marked this case as closed in LegalEase.",
};

export default function ClientDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "there").split(" ")[0];

  const { data: cases, isLoading } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });
  // The most recently updated case is "your case"; others are listed below it.
  const sorted = [...(cases || [])].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
  const main = sorted[0];

  const detail = useQuery({ queryKey: ["case", main?.id], queryFn: () => casesApi.get(main.id), enabled: !!main });
  const timeline = useQuery({ queryKey: ["case-timeline", main?.id], queryFn: () => casesApi.timeline(main.id), enabled: !!main });
  const docs = useQuery({ queryKey: ["case-documents", main?.id], queryFn: () => casesApi.listDocuments(main.id), enabled: !!main });

  const lawyer = detail.data?.lawyer_name;

  return (
    <AppShell
      eyebrow={<Today />}
      title={`Assalam-o-alaikum, ${firstName}.`}
      subtitle={lawyer && <>Represented by <span className="font-semibold text-ds-text">{lawyer}</span></>}
      headerActions={
        <Link to={ROUTES.DOCUMENTS} className="ds-btn-primary">
          Upload a document
        </Link>
      }
    >
      {isLoading ? (
        <p className="flex items-center gap-3 ds-body text-ds-text-2">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading your case…
        </p>
      ) : !main ? (
        <section className="ds-section">
          <h2 className="ds-h3">No case shared with you yet</h2>
          <p className="ds-body text-ds-text-2 mt-2 max-w-[640px]">
            When your lawyer opens your case in LegalEase and links it to this account, it appears here. Meanwhile you
            can ask the AI about Pakistani law or upload documents for a plain-language summary.
          </p>
        </section>
      ) : (
        <>
          <section className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px] border-t-2 border-ds-ink border-b border-b-ds-rule">
            <div className="py-7 min-w-0">
              <p className="ds-eyebrow">Your case</p>
              <Link
                to={`/cases/${main.id}`}
                className="block mt-2 font-ds-serif font-medium text-[32px] leading-[40px] text-ds-text hover:underline decoration-ds-underline decoration-2 underline-offset-4"
              >
                {main.title}
              </Link>
              <p className="ds-body text-ds-text-2 mt-2">
                {[main.case_number, TYPE_LABEL[main.case_type] || main.case_type, main.court_code,
                  main.filing_date && `filed ${fmtDate(main.filing_date)}`]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {isUpcoming(main.next_hearing_date) && main.status !== "closed" && (
                <p className="mt-3 font-ds-sans font-semibold text-[17px] text-ds-seal">
                  Next hearing: {fmtDate(main.next_hearing_date)}
                </p>
              )}
            </div>
            <div className="py-7 lg:pl-8 lg:border-l border-ds-rule">
              <p className="ds-body text-ds-text-2">Current stage</p>
              <p className="font-ds-serif font-medium text-[32px] leading-[40px] mt-1">{STATUS[main.status]?.label}</p>
              <p className="ds-body text-ds-text-2 mt-1">Updated {fmtDate(main.updated_at)}</p>
            </div>
          </section>

          <section className="mt-12">
            <h2 className="ds-h3">Where your case stands</h2>
            <Stepper status={main.status} />
            <div className="mt-6 bg-ds-sheet border border-ds-rule rounded-ds px-6 py-5 max-w-[860px]">
              <p className="ds-eyebrow">About this stage</p>
              <p className="ds-body mt-2 text-[17px] leading-[28px]">{STAGE_NOTE[main.status]}</p>
            </div>
          </section>

          <div className="mt-12 grid gap-12 lg:grid-cols-2">
            <RuledSection
              title="Documents on your case"
              action={docs.data?.length > 0 && <ViewAll to={`/cases/${main.id}`}>Open case</ViewAll>}
            >
              {!docs.data || docs.data.length === 0 ? (
                <p className="ds-body text-ds-text-2 py-5">No documents on this case yet.</p>
              ) : (
                <ul>
                  {docs.data.slice(0, 5).map((d) => (
                    <li key={d.id} className="flex items-center justify-between gap-4 min-h-[56px] border-b border-ds-rule">
                      <span className="ds-body truncate">{d.filename}</span>
                      {d.summary ? (
                        <span className="ds-tag-pass h-7 shrink-0">
                          <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
                          Analysed
                        </span>
                      ) : (
                        <span className="ds-meta shrink-0">Uploaded {fmtDate(d.created_at)}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </RuledSection>

            <RuledSection title="Recent activity">
              {!timeline.data || timeline.data.length === 0 ? (
                <p className="ds-body text-ds-text-2 py-5">No activity yet.</p>
              ) : (
                <ul>
                  {timeline.data
                    .map(readableTimelineEntry)
                    .slice(-4)
                    .reverse()
                    .map((e, i) => (
                      <li key={i} className="py-4 border-b border-ds-rule">
                        <p className="flex justify-between gap-4">
                          <span className="font-ds-sans font-semibold text-[16px]">{e.title}</span>
                          <span className="ds-meta shrink-0">{fmtDate(e.timestamp)}</span>
                        </p>
                        {e.description && <p className="ds-body text-ds-text-2 mt-0.5">{e.description}</p>}
                      </li>
                    ))}
                </ul>
              )}
            </RuledSection>
          </div>

          {sorted.length > 1 && (
            <RuledSection title="Your other cases" className="mt-12">
              <ul>
                {sorted.slice(1).map((c) => (
                  <li key={c.id} className="flex items-center justify-between gap-4 py-4 border-b border-ds-rule">
                    <Link to={`/cases/${c.id}`} className="font-ds-sans font-semibold text-[17px] hover:underline decoration-ds-underline decoration-2 underline-offset-4">
                      {c.title}
                    </Link>
                    <StatusTag status={c.status} />
                  </li>
                ))}
              </ul>
            </RuledSection>
          )}
        </>
      )}
    </AppShell>
  );
}

// Five stages from the case's real status: done in ink, current in Seal
// (the active step), later ones in rule.
function Stepper({ status }) {
  const current = STAGES.indexOf(status);
  return (
    <ol className="mt-5 grid grid-cols-2 sm:grid-cols-5 gap-x-3 gap-y-5">
      {STAGES.map((s, i) => {
        const state = i < current ? "done" : i === current ? "now" : "later";
        return (
          <li key={s} aria-current={state === "now" ? "step" : undefined}>
            <span
              className={`block h-1.5 rounded-ds-sm ${
                state === "done" ? "bg-ds-ink" : state === "now" ? "bg-ds-seal" : "bg-ds-rule"
              }`}
            />
            <span className={`block mt-3 font-ds-sans font-semibold text-[16px] ${state === "later" ? "text-ds-text-2" : "text-ds-text"}`}>
              {STATUS[s].label}
            </span>
            <span className="ds-meta">{state === "now" ? "Now" : state === "done" ? "Done" : ""}</span>
          </li>
        );
      })}
    </ol>
  );
}
