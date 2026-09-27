import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { chatApi } from "@/features/chatbot/api";
import StatusTag from "@/features/case-management/StatusTag";
import { TYPE_LABEL, fmtDate } from "@/features/case-management/caseMeta";
import { Figures, RuledSection, ViewAll, SessionList, Today } from "./components/DashParts";

// Lawyer dashboard — design system v1, per docs/design_reference page 4.
// Adapted to what exists: no calendar, cause list, deadlines or global
// search (none are built); figures and lists come from the real caseload.

export default function LawyerDashboard() {
  const { user } = useAuthStore();
  const firstName = (user?.full_name || "Counsel").split(" ")[0];

  const { data: cases, isLoading } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });
  const { data: sessions } = useQuery({ queryKey: ["chat-sessions"], queryFn: chatApi.listSessions });

  const all = cases || [];
  const open = all.filter((c) => c.status !== "closed");
  const hearing = all.filter((c) => c.status === "hearing_scheduled");
  const dash = isLoading ? "—" : null;

  return (
    <AppShell
      eyebrow={<Today />}
      title={`Assalam-o-alaikum, ${firstName}.`}
      headerActions={
        <Link to={ROUTES.CASES} state={{ create: true }} className="ds-btn-primary">
          New case
        </Link>
      }
    >
      <Figures
        items={[
          { label: "Open cases", value: dash ?? open.length, helper: `${all.length} in total` },
          { label: "Hearing scheduled", value: dash ?? hearing.length, helper: "cases at that stage" },
          { label: "Closed", value: dash ?? all.length - open.length, helper: "all time" },
          { label: "AI conversations", value: sessions ? sessions.length : "—", helper: "in AI Chat" },
        ]}
      />

      <div className="mt-12 grid gap-12 lg:grid-cols-[minmax(0,1fr)_340px]">
        <RuledSection title="Open cases" action={open.length > 0 && <ViewAll to={ROUTES.CASES}>All cases</ViewAll>}>
          {isLoading ? (
            <p className="flex items-center gap-3 ds-body text-ds-text-2 py-5">
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> Loading…
            </p>
          ) : open.length === 0 ? (
            <p className="ds-body text-ds-text-2 py-5">No open cases. Use “New case” to open one.</p>
          ) : (
            <ul>
              {open.slice(0, 6).map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-4 py-4 border-b border-ds-rule">
                  <div className="min-w-0">
                    <Link
                      to={`/cases/${c.id}`}
                      className="block font-ds-sans font-semibold text-[17px] leading-[24px] text-ds-text truncate hover:underline decoration-ds-underline decoration-2 underline-offset-4"
                    >
                      {c.title}
                    </Link>
                    <span className="ds-meta">
                      {[TYPE_LABEL[c.case_type] || c.case_type, c.court_code, `updated ${fmtDate(c.updated_at)}`]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </div>
                  <StatusTag status={c.status} />
                </li>
              ))}
            </ul>
          )}
        </RuledSection>

        <div className="space-y-12">
          <RuledSection title="Hearing scheduled">
            {hearing.length === 0 ? (
              <p className="ds-body text-ds-text-2 py-5">No cases at the hearing stage.</p>
            ) : (
              <ul>
                {hearing.map((c) => (
                  <li key={c.id} className="py-4 border-b border-ds-rule">
                    <Link to={`/cases/${c.id}`} className="font-ds-sans font-semibold text-[17px] leading-[24px] hover:underline decoration-ds-underline decoration-2 underline-offset-4">
                      {c.title}
                    </Link>
                    <span className="ds-meta block">{c.court_code || TYPE_LABEL[c.case_type]}</span>
                  </li>
                ))}
              </ul>
            )}
          </RuledSection>

          <RuledSection title="Recent AI chats" action={sessions?.length > 0 && <ViewAll to={ROUTES.CHATBOT}>Open AI Chat</ViewAll>}>
            <SessionList sessions={sessions} />
          </RuledSection>
        </div>
      </div>
    </AppShell>
  );
}
