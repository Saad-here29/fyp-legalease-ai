import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Plus,
  Briefcase,
  Loader2,
  AlertCircle,
} from "lucide-react";
import DashboardLayout from "@/layouts/DashboardLayout";
import PanelCard from "@/features/dashboard/components/PanelCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/authStore";
import { ROLES, CASE_TYPES } from "@/constants";
import { casesApi } from "./api";

const STATUS_VARIANT = {
  CREATED: "outline",
  ASSIGNED: "secondary",
  IN_PROGRESS: "default",
  HEARING_SCHEDULED: "gold",
  CLOSED: "success",
};

export default function CasesPage() {
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const [showCreate, setShowCreate] = useState(false);

  const { data: cases, isLoading, isError, error } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  return (
    <DashboardLayout
      title="Cases"
      subtitle={isLawyer ? "Your caseload" : "Cases shared with you by your counsel"}
    >
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-muted-foreground">
          {isLoading
            ? "Loading..."
            : `${cases?.length ?? 0} case${cases?.length === 1 ? "" : "s"}`}
        </p>
        {isLawyer && (
          <Button onClick={() => setShowCreate((v) => !v)}>
            <Plus className="h-4 w-4" />
            New case
          </Button>
        )}
      </div>

      {isLawyer && showCreate && (
        <div className="mb-6">
          <CreateCaseForm onDone={() => setShowCreate(false)} />
        </div>
      )}

      {isLoading && (
        <PanelCard>
          <div className="flex items-center gap-2 text-muted-foreground py-8 justify-center">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading cases...
          </div>
        </PanelCard>
      )}

      {isError && (
        <PanelCard>
          <div className="flex items-start gap-3 py-4 text-sm">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Couldn't load cases.</p>
              <p className="text-muted-foreground mt-1">
                {error?.response?.data?.error?.message ||
                  "Make sure the backend is running."}
              </p>
            </div>
          </div>
        </PanelCard>
      )}

      {!isLoading && !isError && cases?.length === 0 && (
        <PanelCard>
          <div className="text-center py-12">
            <Briefcase className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="font-semibold">No cases yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              {isLawyer
                ? "Click \"New case\" above to file your first matter."
                : "Your lawyer will share cases with you here."}
            </p>
          </div>
        </PanelCard>
      )}

      {!isLoading && !isError && cases?.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          {cases.map((c) => (
            <CaseCard key={c.id} case={c} />
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

function CaseCard({ case: c }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm hover:border-accent/40 transition-colors"
    >
      <Link to={`/cases/${c.id}`} className="block p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-xs font-mono text-muted-foreground truncate">
              {c.id.slice(0, 8)}
            </div>
            <h3 className="font-serif text-lg font-semibold truncate mt-0.5">
              {c.title}
            </h3>
          </div>
          <Badge variant={STATUS_VARIANT[c.status] || "default"} className="text-[10px] uppercase tracking-wider">
            {c.status.replace("_", " ")}
          </Badge>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="px-2 py-0.5 rounded bg-secondary/40">{c.case_type}</span>
          {c.court_code && <span>· {c.court_code}</span>}
          {c.filing_date && <span>· filed {c.filing_date}</span>}
        </div>

        {c.description && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {c.description}
          </p>
        )}

        <div className="mt-4 text-xs text-accent font-medium">
          Open case →
        </div>
      </Link>
    </motion.div>
  );
}

function CreateCaseForm({ onDone }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState(CASE_TYPES.DIVORCE);
  const [courtCode, setCourtCode] = useState("");
  const [clientEmail, setClientEmail] = useState("");

  const { mutate, isPending } = useMutation({
    mutationFn: (payload) => casesApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["case-stats"] });
      toast.success("Case created.");
      onDone();
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not create case.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  const submit = (e) => {
    e.preventDefault();
    mutate({
      title,
      description: description || null,
      case_type: caseType,
      court_code: courtCode || null,
      client_email: clientEmail.trim() || null,
    });
  };

  return (
    <PanelCard
      title="New case"
      description="Fill the case details and optionally link a registered client by email — they'll see this case in their dashboard immediately."
    >
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2 space-y-1.5">
          <Label>Title</Label>
          <Input
            placeholder="e.g. Khan v. Khan — Custody"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            minLength={3}
          />
        </div>
        <div className="space-y-1.5">
          <Label>Case type</Label>
          <select
            value={caseType}
            onChange={(e) => setCaseType(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {Object.values(CASE_TYPES).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Court (optional)</Label>
          <Input
            placeholder="Family Court Islamabad"
            value={courtCode}
            onChange={(e) => setCourtCode(e.target.value)}
          />
        </div>
        <div className="sm:col-span-2 space-y-1.5">
          <Label>Client email (optional)</Label>
          <Input
            type="email"
            placeholder="client@example.com"
            value={clientEmail}
            onChange={(e) => setClientEmail(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            If the client is already registered, this case will appear on their
            dashboard. Leave blank to assign later.
          </p>
        </div>
        <div className="sm:col-span-2 space-y-1.5">
          <Label>Description (optional)</Label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Brief summary of the matter..."
          />
        </div>
        <div className="sm:col-span-2 flex gap-2">
          <Button type="submit" variant="gold" disabled={isPending || title.length < 3}>
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create case"}
          </Button>
          <Button type="button" variant="outline" onClick={onDone}>
            Cancel
          </Button>
        </div>
      </form>
    </PanelCard>
  );
}
