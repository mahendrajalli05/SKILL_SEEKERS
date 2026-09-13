import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/system/ScoreDisplay";
import type { EvidenceObject } from "@/lib/types";
import { displayBoundedScore } from "@/lib/display";

function factValue(evidence: EvidenceObject, key: string): string | null {
  const found = evidence.evidence_facts.find((item) => item.key === key);
  if (found == null || found.value == null || found.value === "") {
    return null;
  }
  if (typeof found.value === "object") {
    return JSON.stringify(found.value);
  }
  return String(found.value);
}

function availableFeatures(evidence: EvidenceObject): string {
  const raw = evidence.evidence_facts.find((item) => item.key === "feature_availability")?.value;
  if (raw && typeof raw === "object" && "available" in (raw as object)) {
    const available = (raw as { available?: unknown }).available;
    if (Array.isArray(available) && available.length) {
      return available.map(String).join(", ");
    }
  }
  return "none listed";
}

export function EvidenceCard({ evidence }: { evidence: EvidenceObject }) {
  const score = displayBoundedScore(
    evidence.score,
    evidence.disposition === "NOT_ASSESSABLE" || evidence.disposition === "INCONCLUSIVE"
      ? evidence.disposition
      : evidence.status,
  );
  const isMl = evidence.engine_name === "ml" || evidence.signal_type === "ML_ANOMALY_SIGNAL";
  const modelName = factValue(evidence, "model_name");
  const modelVersion = factValue(evidence, "model_version") || evidence.engine_version;
  const limitations = factValue(evidence, "limitations");
  return (
    <article
      id={`evidence-${evidence.evidence_id}`}
      className={`svk-reveal border p-4 ${
        isMl ? "border-[var(--signal)] bg-[rgba(78,163,255,0.06)]" : "border-[var(--line)] bg-[var(--surface)]"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            {evidence.engine_name} · {evidence.signal_type}
          </p>
          <h3 className="mt-1 font-semibold text-[var(--navy)]">{evidence.finding}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge value={evidence.data_mode} />
          <span className="text-xs uppercase tracking-wide">{evidence.data_mode}</span>
        </div>
      </div>
      {isMl ? (
        <p className="mt-2 text-sm text-[var(--muted)]">
          This is an ML anomaly signal, not fraud confirmation. ml_anomaly_score is
          not a fraud probability and is not Evidence Confidence.
        </p>
      ) : null}
      {score.assessed ? <div className="mt-3"><ScoreBar value={Number(score.label)} /></div> : null}
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">
            {isMl ? "ML anomaly score" : "Score"}
          </dt>
          <dd className="svk-mono">{score.label}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Evidence confidence
          </dt>
          <dd>{Math.round(evidence.confidence * 100)} / 100 (engine 0.0–1.0)</dd>
        </div>
        {isMl ? (
          <>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Model</dt>
              <dd>
                {modelName ?? "unknown"} · {modelVersion}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Feature schema</dt>
              <dd>{factValue(evidence, "feature_schema_version") ?? "unknown"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Training data hash</dt>
              <dd className="break-all">{factValue(evidence, "training_data_hash") ?? "unknown"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Training mode</dt>
              <dd>{factValue(evidence, "training_mode") ?? "unknown"}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Available features</dt>
              <dd>{availableFeatures(evidence)}</dd>
            </div>
          </>
        ) : null}
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Source</dt>
          <dd>{evidence.source_type}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Data mode</dt>
          <dd>{evidence.data_mode}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Disposition</dt>
          <dd className="flex flex-wrap items-center gap-2">
            <StatusBadge value={evidence.status} />
            <span>{evidence.disposition}</span>
          </dd>
        </div>
      </dl>
      <p className="mt-3 text-sm">{evidence.explanation}</p>
      {isMl && limitations ? (
        <p className="mt-2 text-xs text-[var(--muted)]">Limitations: {limitations}</p>
      ) : null}
      {evidence.data_mode !== "REAL" ? (
        <p className="mt-2 text-xs text-[var(--saffron)]">
          This evidence uses SYNTHETIC prototype enrichment and is not official
          MPLADS data.
        </p>
      ) : null}
    </article>
  );
}
