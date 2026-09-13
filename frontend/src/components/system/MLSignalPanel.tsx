import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AnomalyScale, ContributionBars } from "@/components/system/VisualKit";
import { FEATURE_EXPLANATIONS, ML_NOT_FRAUD } from "@/lib/explanations";
import type { MlSignal } from "@/lib/types";

export function MLSignalPanel({
  signal,
  title = "ML ANOMALY SIGNAL",
}: {
  signal?: MlSignal | null;
  title?: string;
}) {
  if (!signal) {
    return (
      <section className="svk-panel p-5">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">{title}</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">{FEATURE_EXPLANATIONS.ml}</p>
        <PageState kind="unavailable" message="No ML anomaly signal is available for this assessment." compact />
        <p className="mt-2 text-sm">{ML_NOT_FRAUD}</p>
      </section>
    );
  }
  return (
    <section className="svk-card p-5" data-tone="violet">
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--violet)]">ML / AI</p>
      <h2 className="svk-display mt-1 text-xl font-semibold text-[var(--navy)]">{title}</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">{FEATURE_EXPLANATIONS.ml}</p>
      <p className="svk-mono mt-4 text-4xl font-semibold text-[var(--violet)]">
        {signal.ml_anomaly_score == null ? "INCONCLUSIVE" : signal.ml_anomaly_score}
      </p>
      <p className="text-xs text-[var(--muted)]">Score / 100</p>
      <div className="mt-4">
        <AnomalyScale score={signal.ml_anomaly_score} />
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Status</dt>
          <dd>
            <StatusBadge value={signal.status} /> {signal.decision_label ?? "unavailable"}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Model</dt>
          <dd>{signal.model_name}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Version</dt>
          <dd className="break-all">{signal.model_version ?? "unavailable"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Feature schema</dt>
          <dd>{signal.feature_schema_version ?? "unavailable"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Training data hash</dt>
          <dd className="break-all">{signal.training_data_hash ?? "unavailable"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Data mode</dt>
          <dd>
            <StatusBadge value={signal.data_mode} /> {signal.training_mode}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Feature availability</dt>
          <dd>{(signal.feature_availability.available || []).join(", ") || "none listed"}</dd>
        </div>
      </dl>
      <p className="mt-4 text-sm">{signal.explanation}</p>
      {signal.contributions?.length ? (
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-semibold text-[var(--navy)]">WHY?</h3>
          <ContributionBars
            items={(signal.contributions ?? []).map((item) => ({
              label: item.feature,
              value: Math.abs(item.contribution) * 100,
            }))}
          />
        </div>
      ) : null}
      <p className="mt-3 text-sm font-medium text-[var(--navy)]">{ML_NOT_FRAUD}</p>
      {signal.limitations.length ? (
        <ul className="mt-3 list-disc pl-5 text-sm text-[var(--muted)]">
          {signal.limitations.slice(0, 6).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
