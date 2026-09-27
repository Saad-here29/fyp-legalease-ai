import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertCircle, Check } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { researchApi } from "./api";

// One statute passage from a research search — design system v1. The AI
// analysis runs on request ("Analyse with AI"), not on every open, to spare
// the shared Groq token budget. The analysis API's "judgment" field holds
// "the operative rule that emerges from the passage" (research_service.py),
// so it's labelled that way — the library holds no judgments.

const FIELDS = [
  ["issue", "Issue"],
  ["findings", "What the statute provides"],
  ["judgment", "Operative rule"],
  ["legal_basis", "Legal basis"],
  ["relevance", "Relevance to your search"],
];

export default function ResearchDetailPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const result = location.state?.result;
  const back = (
    <button onClick={() => navigate(-1)} className="ds-link font-medium">
      Research results
    </button>
  );

  if (!result) {
    return (
      <AppShell eyebrow={<Link to={ROUTES.RESEARCH} className="ds-link font-medium">Research</Link>} title="Research result">
        <p className="flex items-start gap-2 ds-body text-ds-text-2 max-w-[640px]">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
          This passage was opened directly. Passages open from a search — run a search and choose a result.
        </p>
      </AppShell>
    );
  }

  const text = result.text || result.excerpt || "";

  return (
    <AppShell
      eyebrow={back}
      title={result.title}
      subtitle={["Statute", !/^From: .*\(LegalEase corpus\)$/.test(result.citation || "") && result.citation, result.relevance != null && `${Math.round(result.relevance * 100)}% match`]
        .filter(Boolean)
        .join(" · ")}
    >
      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_320px] items-start">
        <div className="space-y-12 min-w-0">
          <Analysis result={result} text={text} autoStart={!!location.state?.analyse} />

          <section>
            <h2 className="ds-h3 pb-3 border-b-2 border-ds-ink">Passage</h2>
            <div className="mt-5 bg-ds-sheet border border-ds-rule rounded-ds p-6 ds-body text-[17px] leading-[28px] whitespace-pre-wrap">
              {text}
            </div>
            <p className="ds-meta mt-3">
              {text.length.toLocaleString()} characters · one excerpt of about 800 characters from the statute as indexed
              by LegalEase, not the whole Act.
            </p>
          </section>
        </div>

        {isLawyer && <SaveToCase result={result} />}
      </div>
    </AppShell>
  );
}

function Analysis({ result, text, autoStart }) {
  // A query enabled on request (not a mutation fired from an effect): it
  // survives React StrictMode's mount/unmount/remount in development, and
  // reopening the same passage reuses the result instead of spending tokens.
  const [requested, setRequested] = useState(autoStart);
  const analyse = useQuery({
    queryKey: ["research-analysis", result.id, result.user_query || ""],
    queryFn: () => researchApi.analyze({ text, source: result.title, user_query: result.user_query || null }),
    enabled: requested,
    staleTime: Infinity,
    retry: false,
  });
  useEffect(() => {
    if (analyse.isError) {
      toast.error(analyse.error?.response?.data?.error?.message || "Could not generate analysis.", {
        description: analyse.error?.response?.data?.error?.hint,
      });
    }
  }, [analyse.isError, analyse.error]);

  const a = analyse.data;
  const busy = analyse.isFetching;
  const run = () => (requested ? analyse.refetch() : setRequested(true));

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3 pb-3 border-b-2 border-ds-ink">
        <h2 className="ds-h3">AI analysis</h2>
        {a ? (
          <span className="ds-tag-neutral">AI-generated · read with the passage</span>
        ) : null}
      </div>

      {busy && (
        <p className="flex items-center gap-3 ds-body text-ds-text-2 py-6">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          Analysing this passage…
        </p>
      )}

      {!a && !busy && (
        <div className="py-6">
          <p className="ds-body text-ds-text-2 max-w-[600px]">
            {analyse.isError
              ? "The analysis couldn't be generated. Try again in a minute."
              : "Get a plain-language breakdown of this passage: the issue, what the statute provides, the operative rule, its legal basis and how it bears on your search."}
          </p>
          <button className="ds-btn-primary mt-5" onClick={run}>
            {analyse.isError ? "Try again" : "Analyse with AI"}
          </button>
        </div>
      )}

      {a && !busy && FIELDS.slice(1).every(([k]) => !a[k] || a[k] === "—") && (
        // The model declined (e.g. the passage doesn't bear on the search):
        // the parser then has only the "Issue" line, so show it as a note.
        <div className="py-6">
          <p className="ds-body text-ds-text-2 max-w-[640px]">
            The AI didn&apos;t produce an analysis of this passage: <span className="text-ds-text">{a.issue}</span>
          </p>
          <button className="ds-btn-secondary mt-5" onClick={run}>
            Try again
          </button>
        </div>
      )}

      {a && !busy && !FIELDS.slice(1).every(([k]) => !a[k] || a[k] === "—") && (
        <>
          <dl>
            {FIELDS.map(([key, label]) => (
              <div key={key} className="grid sm:grid-cols-[200px_1fr] gap-x-6 gap-y-1 py-4 border-b border-ds-rule">
                <dt className="font-ds-sans font-semibold text-[15px] leading-[26px] text-ds-text-2">{label}</dt>
                <dd className="ds-body whitespace-pre-wrap">{a[key] || "—"}</dd>
              </div>
            ))}
          </dl>
          <button className="ds-btn-secondary mt-5" onClick={run}>
            Regenerate
          </button>
        </>
      )}
    </section>
  );
}

function SaveToCase({ result }) {
  const [caseId, setCaseId] = useState("");
  const [savedTo, setSavedTo] = useState(null);
  const { data: cases } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });

  const save = useMutation({
    mutationFn: (id) =>
      casesApi.saveResearch(id, {
        title: result.title,
        citation: result.citation || null,
        excerpt: result.excerpt || null,
        source_id: result.id,
      }),
    onSuccess: (_, id) => {
      setSavedTo((cases || []).find((c) => c.id === id)?.title || "the case");
      toast.success("Saved to case.", { description: "It appears on the case timeline as a research note." });
    },
    onError: (e) =>
      toast.error(e?.response?.data?.error?.message || "Could not save to case.", {
        description: e?.response?.data?.error?.hint,
      }),
  });

  const open = (cases || []).filter((c) => c.status !== "closed");

  return (
    <aside className="bg-ds-sheet border border-ds-rule rounded-ds p-6">
      <h2 className="ds-h4">Save to a case</h2>
      <p className="ds-meta mt-1">Adds this passage to the case timeline as a research note.</p>
      {open.length === 0 ? (
        <p className="ds-body text-ds-text-2 mt-4">You have no open cases. Create one from the Cases page first.</p>
      ) : (
        <div className="mt-4 space-y-3">
          <label htmlFor="save-case" className="sr-only">Case</label>
          <select id="save-case" value={caseId} onChange={(e) => setCaseId(e.target.value)} className="ds-input">
            <option value="">Select a case…</option>
            {open.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
          <button
            className="ds-btn-secondary w-full min-h-[48px]"
            disabled={!caseId || save.isPending}
            onClick={() => save.mutate(caseId)}
          >
            {save.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Saving" /> : "Save to case"}
          </button>
          {savedTo && (
            <p className="flex items-center gap-1.5 font-ds-sans font-semibold text-[14px] text-ds-pass">
              <Check className="h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
              Saved to {savedTo}
            </p>
          )}
        </div>
      )}
    </aside>
  );
}
