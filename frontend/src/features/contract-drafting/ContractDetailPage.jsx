import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  ShieldCheck,
  Check,
  X,
  History,
} from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import AppButton from "@/components/ui/AppButton";
import { useAuthStore } from "@/store/authStore";
import { ROLES, ROUTES } from "@/constants";
import MarkdownBlocks from "@/lib/MarkdownBlocks";
import { contractsApi } from "./api";
import { CONTRACT_TEMPLATES } from "./templates";

export default function ContractDetailPage() {
  const { id } = useParams();
  const { user } = useAuthStore();
  const isLawyer = user?.role === ROLES.LAWYER;
  const qc = useQueryClient();

  const contractQuery = useQuery({
    queryKey: ["contract", id],
    queryFn: () => contractsApi.get(id),
  });
  const versionsQuery = useQuery({
    queryKey: ["contract-versions", id],
    queryFn: () => contractsApi.versions(id),
    enabled: !!contractQuery.data,
  });

  const [selectedVersionNumber, setSelectedVersionNumber] = useState(null);
  const [complianceResult, setComplianceResult] = useState(null);

  const checkCompliance = useMutation({
    mutationFn: (versionNumber) =>
      contractsApi.checkCompliance(id, versionNumber),
    onSuccess: (result) => {
      setComplianceResult(result);
      qc.invalidateQueries({ queryKey: ["contract-versions", id] });
      toast.success(
        result.all_passed
          ? "All required clauses found."
          : "Some required clauses are missing."
      );
    },
    onError: (e) => {
      toast.error(
        e?.response?.data?.error?.message || "Could not run compliance check.",
        { description: e?.response?.data?.error?.hint }
      );
    },
  });

  if (contractQuery.isLoading) {
    return (
      <AppShell title="Contract">
        <div className="flex items-center justify-center gap-2 py-12 text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading contract…
        </div>
      </AppShell>
    );
  }

  if (contractQuery.isError) {
    return (
      <AppShell title="Contract">
        <div className="max-w-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-brick shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-ink-text">
                {contractQuery.error?.response?.data?.error?.message ||
                  "Could not load this contract."}
              </p>
              <Link
                to={ROUTES.CONTRACTS}
                className="text-sm text-brick hover:underline underline-offset-2 mt-2 inline-block"
              >
                ← Back to all contracts
              </Link>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  const contract = contractQuery.data;
  const versions = versionsQuery.data || [];
  const label = CONTRACT_TEMPLATES[contract.contract_type]?.label || contract.contract_type;

  const activeVersion =
    versions.find((v) => v.version_number === selectedVersionNumber) ||
    contract.latest_version;

  // A fresh check-compliance result (local state) takes priority over
  // whatever was already stored on the version from a previous check.
  const displayedCompliance =
    complianceResult && complianceResult.version_number === activeVersion.version_number
      ? complianceResult
      : activeVersion.compliance_result;

  return (
    <AppShell title={contract.title || label} subtitle={`${label} · v${activeVersion.version_number}`}>
      <Link
        to={ROUTES.CONTRACTS}
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink-text mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        All contracts
      </Link>

      <div className="grid gap-10 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-8">
          <section>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h2 className="font-editorial text-xl text-ink-text">Contract text</h2>
              {isLawyer && (
                <AppButton
                  variant="secondary"
                  disabled={checkCompliance.isPending}
                  onClick={() => checkCompliance.mutate(activeVersion.version_number)}
                  className="shrink-0"
                >
                  {checkCompliance.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Checking…
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4" />
                      Check compliance
                    </>
                  )}
                </AppButton>
              )}
            </div>
            <div className="border-t border-hairline pt-5">
              <MarkdownBlocks text={activeVersion.content} />
            </div>
          </section>

          {displayedCompliance && (
            <section>
              <h2 className="font-editorial text-xl text-ink-text mb-1">
                Compliance check
              </h2>
              <p className="text-sm text-ink-muted mb-3">
                {displayedCompliance.all_passed
                  ? "All required clauses were found in this version."
                  : "One or more required clauses were not found — deterministic keyword check, not another AI call."}
              </p>
              <ul className="border-t border-hairline">
                {displayedCompliance.results.map((r) => (
                  <li
                    key={r.name}
                    className="py-3 border-b border-hairline-subtle flex items-start gap-3"
                  >
                    {r.passed ? (
                      <Check className="h-4 w-4 text-status-active shrink-0 mt-0.5" />
                    ) : (
                      <X className="h-4 w-4 text-brick shrink-0 mt-0.5" />
                    )}
                    <div className="min-w-0">
                      <div className="text-sm text-ink-text">{r.name}</div>
                      {r.matched_snippet && (
                        <div className="text-xs text-ink-muted mt-0.5 italic">
                          "…{r.matched_snippet}…"
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <div>
          <h2 className="font-editorial text-xl text-ink-text mb-1">Version history</h2>
          <p className="text-sm text-ink-muted mb-3">
            {versions.length} version{versions.length === 1 ? "" : "s"}
          </p>
          <ul className="border-t border-hairline">
            {(versions.length ? versions : [contract.latest_version])
              .slice()
              .reverse()
              .map((v) => (
                <li key={v.id} className="border-b border-hairline-subtle last:border-0">
                  <button
                    onClick={() => setSelectedVersionNumber(v.version_number)}
                    className={`w-full text-left py-3 px-2 -mx-2 flex items-center gap-2.5 transition-colors ${
                      v.version_number === activeVersion.version_number
                        ? "bg-hairline-subtle/60"
                        : "hover:bg-hairline-subtle/40"
                    }`}
                  >
                    <History className="h-3.5 w-3.5 text-ink-muted shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm text-ink-text">Version {v.version_number}</div>
                      <div className="text-xs text-ink-muted">
                        {new Date(v.created_at).toLocaleString()}
                      </div>
                    </div>
                  </button>
                </li>
              ))}
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
