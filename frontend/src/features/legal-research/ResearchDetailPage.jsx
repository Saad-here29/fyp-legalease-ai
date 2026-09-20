import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  BookOpen,
  Bookmark,
  Loader2,
  AlertCircle,
  Sparkles,
  Gavel,
  Scale,
  Target,
  Lightbulb,
  ListChecks,
} from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { researchApi } from "./api";
import { cnInput } from "@/lib/formStyles";

export default function ResearchDetailPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;

  const result = location.state?.result;

  if (!result) {
    return (
      <AppShell title="Research result">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-ink-text">This result was opened directly.</p>
            <p className="text-ink-muted mt-1">
              Detail snapshots are loaded from the search list. Run a search
              and click "Read more" again.
            </p>
            <Link
              to={ROUTES.RESEARCH}
              className="inline-flex items-center gap-1.5 text-sm text-brick hover:underline underline-offset-2 mt-3"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to research
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={result.title}
      subtitle={`${result.case_type === "judgment" ? "Judgment" : "Statute"}${
        result.year ? ` · ${result.year}` : ""
      }${result.court ? ` · ${result.court}` : ""}`}
    >
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink-text mb-8"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to results
      </button>

      <div className="mb-10">
        <StructuredAnalysisPanel result={result} />
      </div>

      <div className="grid gap-10 lg:grid-cols-3">
        <PanelCard className="lg:col-span-2" title="Original passage">
          <div className="flex items-center gap-2 mb-3 text-xs text-ink-muted">
            <BookOpen className="h-4 w-4" />
            <span>{result.case_type === "judgment" ? "Judgment" : "Statute"}</span>
            {result.citation && <span>{result.citation}</span>}
            {result.relevance != null && (
              <span className="ml-auto">{Math.round(result.relevance * 100)}% relevance</span>
            )}
          </div>

          <div className="text-sm leading-relaxed text-ink-text whitespace-pre-wrap max-h-[60vh] overflow-y-auto pr-2">
            {result.text || result.excerpt}
          </div>

          <div className="mt-6 pt-4 border-t border-hairline-subtle text-xs text-ink-muted">
            <span className="font-medium text-ink-text">
              {(result.text || result.excerpt || "").length.toLocaleString()} characters
            </span>{" "}
            — This passage is one chunk from the LegalEase corpus
            (800-char chunks with 100-char overlap). Open the original PDF
            for the full statutory text or judgment.
          </div>
        </PanelCard>

        <div className="space-y-10">
          {isLawyer && <SaveToCase result={result} />}

          <PanelCard title="Source">
            <div className="text-sm">
              <div className="font-medium text-ink-text">{result.title}</div>
              {result.citation && <div className="text-xs text-ink-muted mt-1">{result.citation}</div>}
              {result.court && (
                <div className="text-xs text-ink-muted mt-2">
                  Court: <span className="text-ink-text">{result.court}</span>
                </div>
              )}
              {result.year && (
                <div className="text-xs text-ink-muted mt-0.5">
                  Year: <span className="text-ink-text">{result.year}</span>
                </div>
              )}
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}

function StructuredAnalysisPanel({ result }) {
  const analyzeMutation = useMutation({
    mutationFn: () =>
      researchApi.analyze({
        text: result.text || result.excerpt || "",
        source: result.title,
        user_query: result.user_query || null,
      }),
    onError: (e) => {
      toast.error(e?.response?.data?.error?.message || "Could not generate analysis.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  useEffect(() => {
    if (!analyzeMutation.isPending && !analyzeMutation.data && !analyzeMutation.isError) {
      analyzeMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const a = analyzeMutation.data;

  return (
    <PanelCard
      title="Structured legal analysis"
      description="AI-generated breakdown grounded in the passage below."
      action={
        <button
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending}
          className="text-xs text-brick hover:underline underline-offset-2 disabled:text-ink-muted disabled:no-underline flex items-center gap-1"
        >
          {analyzeMutation.isPending ? (
            "Analysing…"
          ) : a ? (
            <>
              <Sparkles className="h-3 w-3" /> Regenerate
            </>
          ) : (
            <>
              <Sparkles className="h-3 w-3" /> Generate analysis
            </>
          )}
        </button>
      }
    >
      {analyzeMutation.isPending && (
        <div className="flex flex-col items-center gap-3 py-8 text-sm text-ink-muted">
          <Loader2 className="h-5 w-5 animate-spin" />
          <div className="text-center">
            <p className="font-medium text-ink-text">Analysing this passage…</p>
            <p className="text-xs mt-1">
              Llama-3.3 is structuring the Issue, Findings, Judgment,
              Legal Basis and Relevance. Usually 2–4 seconds.
            </p>
          </div>
        </div>
      )}

      {!a && !analyzeMutation.isPending && analyzeMutation.isError && (
        <p className="text-sm text-brick">
          Could not generate the analysis. Click <strong>Regenerate</strong> to retry.
        </p>
      )}

      {a && (
        <div className="grid gap-5 sm:grid-cols-2">
          <AnalysisField icon={Target} label="Issue" value={a.issue} />
          <AnalysisField icon={ListChecks} label="Findings" value={a.findings} />
          <AnalysisField icon={Gavel} label="Judgment" value={a.judgment} />
          <AnalysisField icon={Scale} label="Legal basis" value={a.legal_basis} />
          <AnalysisField
            icon={Lightbulb}
            label="Relevance"
            value={a.relevance}
            className="sm:col-span-2"
          />
        </div>
      )}
    </PanelCard>
  );
}

function AnalysisField({ icon: Icon, label, value, className = "" }) {
  return (
    <div className={`pb-4 border-b border-hairline-subtle ${className}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <Icon className="h-3.5 w-3.5 text-ink-muted" />
        <span className="text-xs text-ink-muted">{label}</span>
      </div>
      <p className="text-sm leading-relaxed text-ink-text whitespace-pre-wrap">{value || "—"}</p>
    </div>
  );
}

function SaveToCase({ result }) {
  const [selectedCaseId, setSelectedCaseId] = useState("");

  const { data: cases } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const saveMutation = useMutation({
    mutationFn: (caseId) =>
      casesApi.saveResearch(caseId, {
        title: result.title,
        citation: result.citation || null,
        excerpt: result.excerpt || null,
        source_id: result.id,
      }),
    onSuccess: () => {
      toast.success("Saved to case.", {
        description: "It will appear on the case timeline as a research note.",
      });
    },
    onError: (e) => {
      toast.error(e?.response?.data?.error?.message || "Could not save to case.", {
        description: e?.response?.data?.error?.hint,
      });
    },
  });

  const activeCases = (cases || []).filter((c) => c.status !== "closed");

  return (
    <PanelCard
      title="Save to a case"
      description="Attach this authority to one of your open cases — appears on the case timeline."
    >
      {activeCases.length === 0 ? (
        <p className="text-xs text-ink-muted">
          You don't have any open cases. Create one first.
        </p>
      ) : (
        <>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className={cnInput(false)}
          >
            <option value="">Select a case...</option>
            {activeCases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title} · {c.status.replace("_", " ")}
              </option>
            ))}
          </select>
          <AppButton
            disabled={!selectedCaseId || saveMutation.isPending}
            onClick={() => saveMutation.mutate(selectedCaseId)}
            className="w-full mt-3"
          >
            {saveMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Bookmark className="h-4 w-4" />
                Save to case
              </>
            )}
          </AppButton>
        </>
      )}
    </PanelCard>
  );
}
