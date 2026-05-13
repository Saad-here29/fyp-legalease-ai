import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search,
  Loader2,
  BookOpen,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ROUTES } from "@/constants";
import { researchApi } from "./api";

const TYPE_FILTERS = [
  { key: "all", label: "All" },
  { key: "statute", label: "Statutes" },
  { key: "judgment", label: "Judgments" },
];

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [court, setCourt] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const { mutate, data, isPending, isError, error, reset } = useMutation({
    mutationFn: (payload) => researchApi.search(payload),
  });

  const submit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    reset();
    mutate({
      query: query.trim(),
      court: court || null,
      year_from: yearFrom ? Number(yearFrom) : null,
      year_to: yearTo ? Number(yearTo) : null,
      case_type: typeFilter === "all" ? null : typeFilter,
      top_k: 10,
    });
  };

  return (
    <DashboardLayout
      title="AI Legal Research"
      subtitle="Semantic search over Pakistani statutes, Cr.P.C., PPC, and Supreme Court judgments"
    >
      <PanelCard className="mb-6">
        <form onSubmit={submit} className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 flex items-center gap-2 rounded-lg border border-input bg-background px-3">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. khula procedure, FIR registration, child custody, Section 302 PPC..."
                className="flex-1 bg-transparent outline-none py-2 text-sm"
              />
            </div>
            <Button
              type="submit"
              variant="gold"
              size="lg"
              disabled={isPending || !query.trim()}
            >
              {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mr-1">
              Type:
            </span>
            {TYPE_FILTERS.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTypeFilter(t.key)}
                className={`text-xs font-medium px-3 py-1 rounded-full border transition-colors ${
                  typeFilter === t.key
                    ? "bg-legal-gold/15 border-legal-gold/60 text-legal-gold"
                    : "bg-secondary/30 border-border/50 text-muted-foreground hover:border-border"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Court (judgments only)
              </label>
              <Input
                value={court}
                onChange={(e) => setCourt(e.target.value)}
                placeholder="e.g. Supreme Court"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Year from
              </label>
              <Input
                type="number"
                value={yearFrom}
                onChange={(e) => setYearFrom(e.target.value)}
                placeholder="1947"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Year to
              </label>
              <Input
                type="number"
                value={yearTo}
                onChange={(e) => setYearTo(e.target.value)}
                placeholder="2026"
                className="mt-1"
              />
            </div>
          </div>
        </form>
      </PanelCard>

      {isPending && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span className="flex items-center gap-2">
              <Loader2 className="h-3 w-3 animate-spin" />
              Searching 88,036 chunks of Pakistani law...
            </span>
            <span>FAISS · cosine similarity</span>
          </div>
          {[0, 1, 2].map((i) => (
            <SkeletonResult key={i} delay={i * 80} />
          ))}
        </div>
      )}

      {isError && (
        <PanelCard>
          <div className="flex items-start gap-3 py-2">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">Search failed.</p>
              <p className="text-muted-foreground mt-1">
                {error?.response?.data?.error?.message ||
                  "Could not reach the research service. Is the backend running?"}
              </p>
            </div>
          </div>
        </PanelCard>
      )}

      {data && data.results.length === 0 && !isPending && (
        <PanelCard>
          <p className="text-sm text-muted-foreground text-center py-8">
            No matching authorities found. Try different keywords or remove the
            court / year filters.
          </p>
        </PanelCard>
      )}

      {data && data.results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {data.total} result{data.total === 1 ? "" : "s"} for{" "}
            <span className="text-foreground font-medium">"{data.query}"</span>
          </p>
          {data.results.map((r, i) => (
            <ResultCard key={r.id} result={r} index={i} />
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

function ResultCard({ result, index }) {
  const score = Math.round((result.relevance || 0) * 100);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="rounded-xl border border-border/40 bg-card/50 p-5 backdrop-blur-sm hover:border-accent/40 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <BookOpen className="h-3.5 w-3.5 text-accent" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-accent">
              {result.case_type === "judgment" ? "Judgment" : "Statute"}
            </span>
            {result.year && (
              <span className="text-[11px] text-muted-foreground">
                · {result.year}
              </span>
            )}
            {result.court && (
              <span className="text-[11px] text-muted-foreground">
                · {result.court}
              </span>
            )}
          </div>
          <h3 className="font-serif text-lg font-semibold leading-tight">
            {result.title}
          </h3>
          {result.citation && (
            <p className="text-xs font-mono text-muted-foreground mt-0.5">
              {result.citation}
            </p>
          )}
        </div>
        <Badge variant="gold" className="shrink-0">
          {score}% match
        </Badge>
      </div>

      <p className="mt-3 text-sm text-muted-foreground leading-relaxed line-clamp-3">
        {result.excerpt}
      </p>

      <div className="mt-4 flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          asChild
          className="text-accent hover:text-accent hover:bg-accent/10"
        >
          <Link
            to={ROUTES.RESEARCH_DETAIL.replace(
              ":id",
              encodeURIComponent(result.id)
            )}
            state={{ result }}
          >
            Read more <ArrowRight className="h-3.5 w-3.5 ml-1" />
          </Link>
        </Button>
      </div>
    </motion.div>
  );
}

function SkeletonResult({ delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: delay / 1000 }}
      className="rounded-xl border border-border/40 bg-card/50 p-5 backdrop-blur-sm animate-pulse"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="space-y-2 flex-1">
          <div className="h-3 w-24 rounded-full bg-muted/50" />
          <div className="h-5 w-3/4 rounded-md bg-muted/40" />
        </div>
        <div className="h-6 w-20 rounded-full bg-muted/30" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded-md bg-muted/30" />
        <div className="h-3 w-11/12 rounded-md bg-muted/30" />
        <div className="h-3 w-3/5 rounded-md bg-muted/30" />
      </div>
    </motion.div>
  );
}
