import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/system/ScoreDisplay";
import { ContributionBars } from "@/components/system/VisualKit";
import type { ProjectRiskV2Response, RiskV2Group } from "@/lib/types";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { recommendedActionLabel } from "@/lib/display";

function GroupList({
  title,
  items,
  empty,
}: {
  title: string;
  items: RiskV2Group[];
  empty: string;
}) {
  return (
    <section className="border border-[var(--line)] bg-[var(--surface)] p-5">
      <h3 className="font-semibold text-[var(--navy)]">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--muted)]">{empty}</p>
      ) : (
        <ul className="mt-3 space-y-3 text-sm">
          {items.map((item) => (
            <li key={`${item.group_id}-${item.evidence_ids.join(",") || "none"}`}>
              <p className="font-medium text-[var(--navy)]">{item.display_name}</p>
              <p className="text-[0.65rem] uppercase tracking-wide text-[var(--muted)]">
                {item.state.replaceAll("_", " ")}
              </p>
              <ScoreBar value={item.effective_contribution} />
              <p className="text-[var(--muted)]">
                State {item.state.replaceAll("_", " ")} · polarity {item.polarity.replaceAll("_", " ")}
                {item.raw_evidence_score != null ? ` · raw ${item.raw_evidence_score}` : ""}
                {item.confidence != null ? ` · confidence ${item.confidence}` : ""}
                {` · effective ${item.effective_contribution}`}
                {item.correlation_factor < 1 ? ` · correlation keep ${item.correlation_factor}` : ""}
              </p>
              {item.correlation_reason ? (
                <p className="mt-1 text-[var(--muted)]">{item.correlation_reason}</p>
              ) : null}
              {item.unavailable_reason ? (
                <p className="mt-1 text-[var(--muted)]">{item.unavailable_reason}</p>
              ) : null}
              {item.evidence_ids.length > 0 ? (
                <p className="mt-1 break-all text-xs text-[var(--muted)]">
                  Evidence IDs: {item.evidence_ids.join(", ")}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function RiskFusionV2Panel({
  risk,
  loading,
  error,
}: {
  risk?: ProjectRiskV2Response | null;
  loading?: boolean;
  error?: string | null;
}) {
  return (
    <div id="risk-fusion-v2" className="space-y-4">
      <section className="svk-panel p-5">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">Review Priority</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Investigation Priority and Evidence Confidence are review rankings. They
          are not a fraud probability and do not sanction a project or release funds.
        </p>
        <p className="mt-1 text-xs text-[var(--muted)]">{FEATURE_EXPLANATIONS.risk}</p>
        {loading ? <PageState kind="loading" message="Loading V2 fused scores…" compact /> : null}
        {error ? <PageState kind="error" message={error} compact /> : null}
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Investigation Priority
            </p>
            <p className="svk-mono mt-1 text-3xl font-semibold text-[var(--navy)]">
              {risk ? `${risk.investigation_priority}/100` : "Not assessed"}
            </p>
            {risk ? (
              <>
                <p className="text-xs text-[var(--muted)]">Review priority · Class {risk.risk_class}</p>
                <div className="mt-2"><ScoreBar value={risk.investigation_priority} tone="priority" /></div>
              </>
            ) : null}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Evidence Confidence
            </p>
            <p className="svk-mono mt-1 text-3xl font-semibold text-[var(--signal)]">
              {risk ? `${risk.evidence_confidence}/100` : "Not assessed"}
            </p>
            {risk ? <div className="mt-2"><ScoreBar value={risk.evidence_confidence} /></div> : null}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Recommendation
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
        {risk?.evidence_contribution_breakdown?.length ? (
          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold text-[var(--navy)]">Group contributions</h3>
            <ContributionBars
              items={risk.evidence_contribution_breakdown.map((item) => ({
                label: item.display_name,
                value: item.effective_contribution,
                unavailable: item.state.includes("UNAVAILABLE") || item.state.includes("NOT_ASSESSABLE") || item.state.includes("NOT_YET"),
                reason: item.unavailable_reason,
              }))}
            />
          </div>
        ) : null}
        {risk?.synthetic_disclosure ? (
          <p className="mt-3 text-sm text-[var(--saffron)]">{risk.synthetic_disclosure}</p>
        ) : null}
        {risk ? (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <StatusBadge value={risk.data_mode} />
            <p className="text-xs text-[var(--muted)]">
              Data mode {risk.data_mode} · {risk.engine_version}
            </p>
          </div>
        ) : null}
      </section>

      <section className="border border-[var(--line)] bg-white p-5">
        <h3 className="font-semibold text-[var(--navy)]">WHY?</h3>
        <p className="mt-2 text-sm">{risk?.explanation ?? "V2 fused explanation is not yet available."}</p>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Explanation type: {risk?.explanation_type ?? "Not assessed"}
        </p>
        <p className="mt-2 text-sm">{risk?.recommendation}</p>
        {risk ? (
          <>
            <p className="mt-2 text-xs text-[var(--muted)]">{risk.weight_note}</p>
            <p className="mt-1 text-xs text-[var(--muted)]">{risk.note}</p>
          </>
        ) : null}
      </section>

      <GroupList
        title="Evidence contribution breakdown"
        items={risk?.evidence_contribution_breakdown ?? []}
        empty="No V2 evidence groups are currently listed."
      />
      <GroupList
        title="Independent evidence"
        items={risk?.independent_evidence_groups ?? []}
        empty="No independent contributing group is currently available."
      />
      <GroupList
        title="Correlated evidence"
        items={risk?.discounted_correlated_evidence ?? []}
        empty="No correlated evidence was discounted."
      />

      <section className="border border-[var(--line)] bg-white p-5">
        <h3 className="font-semibold text-[var(--navy)]">Conflicting evidence</h3>
        {(risk?.conflicting_evidence ?? []).length === 0 ? (
          <p className="mt-2 text-sm text-[var(--muted)]">No conflicting V2 evidence groups were recorded.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {(risk?.conflicting_evidence ?? []).map((item) => (
              <li key={`${item.left_group}-${item.right_group}`}>
                {item.summary}
              </li>
            ))}
          </ul>
        )}
      </section>

      <GroupList
        title="Unavailable evidence"
        items={risk?.unavailable_evidence ?? []}
        empty="No unavailable V2 groups were listed."
      />
    </div>
  );
}
