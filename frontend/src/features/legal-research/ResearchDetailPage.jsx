import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
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
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import { casesApi } from "@/features/case-management/api";
import { researchApi } from "./api";

export default function ResearchDetailPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;

  // The ResearchPage passes the full result via router state. If the user
  // refreshed or arrived via a deep link, we show a graceful empty state and
  // a button back to /research.
  const result = location.state?.result;

  if (!result) {
    return (
      <DashboardLayout title="Research result">
        <PanelCard>
          <div className="flex items-start gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">This result was opened directly.</p>
              <p className="text-muted-foreground mt-1">
                Detail snapshots are loaded from the search list. Run a search
                and click "Read more" again.
              </p>
              <Button asChild size="sm" variant="outline" className="mt-3">
                <Link to={ROUTES.RESEARCH}>
                  <ArrowLeft className="h-3.5 w-3.5 mr-1" />
                  Back to research
                </Link>
              </Button>
            </div>
          </div>
        </PanelCard>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title={result.title}
      subtitle={`${result.case_type === "judgment" ? "Judgment" : "Statute"}${
        result.year ? ` · ${result.year}` : ""
      }${result.court ? ` · ${result.court}` : ""}`}
    >
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to results
      </button>

      <StructuredAnalysisPanel result={result} />

      <div className="grid gap-6 lg:grid-cols-3 mt-6">
        <PanelCard className="lg:col-span-2" title="Original passage">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-accent" />
            <Badge variant="gold" className="text-[10px] uppercase tracking-wider">
              {result.case_type === "judgment" ? "Judgment" : "Statute"}
            </Badge>
            {result.citation && (
              <span className="text-xs font-mono text-muted-foreground">
                {result.citation}
              </span>
            )}
            {result.relevance != null && (
              <span className="ml-auto text-xs text-muted-foreground">
                {Math.round(result.relevance * 100)}% relevance
              </span>
            )}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm leading-relaxed text-foreground whitespace-pre-wrap max-h-[60vh] overflow-y-auto scrollbar-thin pr-2"
          >
            {result.text || result.excerpt}
          </motion.div>

          <div className="mt-6 pt-4 border-t border-border/40 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">
              {(result.text || result.excerpt || "").length.toLocaleString()} characters
            </span>{" "}
            — This passage is one chunk from the LegalEase corpus
            (800-char chunks with 100-char overlap). Open the original PDF
            for the full statutory text or judgment.
          </div>
        </PanelCard>

        <div className="space-y-4">
          {isLawyer && <SaveToCase result={result} />}

          <PanelCard title="Source">
            <div className="text-sm">
              <div className="font-semibold">{result.title}</div>
              {result.citation && (
                <div className="text-xs text-muted-foreground font-mono mt-1">
                  {result.citation}
                </div>
              )}
              {result.court && (
                <div className="text-xs text-muted-foreground mt-2">
                  Court: <span className="text-foreground">{result.court}</span>
                </div>
              )}
              {result.year && (
                <div className="text-xs text-muted-foreground mt-0.5">
                  Year: <span className="text-foreground">{result.year}</span>
                </div>
              )}
            </div>
          </PanelCard>
        </div>
      </div>
    </DashboardLayout>
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
      toast.error(
        e?.response?.data?.error?.message || "Could not generate analysis.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  // Auto-fire the analysis the moment this page mounts — the user
  // shouldn't have to click a button to see the structured breakdown.
  // We guard with a ref so a re-render doesn't re-trigger.
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
        <Button
          size="sm"
          variant="gold"
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending}
        >
          {analyzeMutation.isPending ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Analysing...
            </>
          ) : a ? (
            <>
              <Sparkles className="h-3.5 w-3.5" />
              Regenerate
            </>
          ) : (
            <>
              <Sparkles className="h-3.5 w-3.5" />
              Generate analysis
            </>
          )}
        </Button>
      }
    >
      {analyzeMutation.isPending && (
        <div className="flex flex-col items-center gap-3 py-8 text-sm text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin text-accent" />
          <div className="text-center">
            <p className="font-medium text-foreground">
              Analysing this passage…
            </p>
            <p className="text-xs mt-1">
              Llama-3.3 is structuring the Issue, Findings, Judgment,
              Legal Basis and Relevance. Usually 2–4 seconds.
            </p>
          </div>
        </div>
      )}

      {!a && !analyzeMutation.isPending && analyzeMutation.isError && (
        <p className="text-sm text-destructive">
          Could not generate the analysis. Click <strong>Regenerate</strong> to
          retry.
        </p>
      )}

      {a && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-4 sm:grid-cols-2"
        >
          <AnalysisField icon={Target} label="Issue" value={a.issue} />
          <AnalysisField icon={ListChecks} label="Findings" value={a.findings} />
          <AnalysisField icon={Gavel} label="Judgment" value={a.judgment} />
          <AnalysisField icon={Scale} label="Legal Basis" value={a.legal_basis} />
          <AnalysisField
            icon={Lightbulb}
            label="Relevance"
            value={a.relevance}
            className="sm:col-span-2"
          />
        </motion.div>
      )}
    </PanelCard>
  );
}

function AnalysisField({ icon: Icon, label, value, className = "" }) {
  return (
    <div
      className={`rounded-lg border border-border/40 bg-background/30 p-4 ${className}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="h-7 w-7 rounded-md bg-accent/15 flex items-center justify-center">
          <Icon className="h-3.5 w-3.5 text-accent" />
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
        {value || "—"}
      </p>
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
      toast.error(
        e?.response?.data?.error?.message || "Could not save to case.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const activeCases = (cases || []).filter((c) => c.status !== "CLOSED");

  return (
    <PanelCard
      title="Save to a case"
      description="Attach this authority to one of your open cases — appears on the case timeline."
    >
      {activeCases.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          You don't have any open cases. Create one first.
        </p>
      ) : (
        <>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select a case...</option>
            {activeCases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title} · {c.status.replace("_", " ")}
              </option>
            ))}
          </select>
          <Button
            variant="gold"
            className="w-full mt-2"
            disabled={!selectedCaseId || saveMutation.isPending}
            onClick={() => saveMutation.mutate(selectedCaseId)}
          >
            {saveMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Bookmark className="h-4 w-4" />
                Save to case
              </>
            )}
          </Button>
        </>
      )}
    </PanelCard>
  );
}
