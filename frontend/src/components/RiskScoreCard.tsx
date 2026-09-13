import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageState } from "@/components/ui/PageState";
import type { ProjectRiskResponse } from "@/lib/types";
import {
  displayEvidenceConfidence,
  displayInvestigationPriority,
  recommendedActionLabel,
} from "@/lib/display";

export function RiskScoreCard({
  risk,
  loading,
  error,
}: {
  risk?: ProjectRiskResponse | null;
  loading?: boolean;
  error?: string | null;
}) {
  const priority = displayInvestigationPriority(risk);
  const confidence = displayEvidenceConfidence(risk);
  return (
    <section className="border border-[var(--line)] bg-[var(--surface)] p-5">
      <h2 className="font-semibold text-[var(--navy)]">Risk display</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Investigation Priority and Evidence Confidence are review rankings. They
        are not a fraud probability.
      </p>
      {loading ? <PageState kind="loading" message="Loading fused scores…" compact /> : null}
      {error ? <PageState kind="error" message={error} compact /> : null}
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Investigation Priority
          </p>
          <p className="mt-1 text-2xl font-semibold text-[var(--navy)]">{priority.label}</p>
          {priority.assessed ? <p className="text-xs text-[var(--muted)]">Scale 0–100</p> : null}
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Evidence Confidence
          </p>
          <p className="mt-1 text-2xl font-semibold text-[var(--navy)]">{confidence.label}</p>
          {confidence.assessed ? <p className="text-xs text-[var(--muted)]">Scale 0–100</p> : null}
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Recommended action
          </p>
          <p className="mt-1 text-2xl font-semibold text-[var(--navy)]">
            {risk ? recommendedActionLabel(risk.recommended_action) : "Not assessed"}
          </p>
          {risk ? (
            <div className="mt-2">
              <StatusBadge value={risk.recommended_action} />
            </div>
          ) : null}
        </div>
      </div>
      {risk ? (
        <div className="mt-4 space-y-2 text-sm">
          <p>
            <span className="font-medium">Explanation type:</span> {risk.explanation_type}
          </p>
          <p>{risk.explanation}</p>
          <p className="text-[var(--muted)]">{risk.weight_note}</p>
          <p className="text-[var(--muted)]">{risk.note}</p>
        </div>
      ) : null}
    </section>
  );
}
