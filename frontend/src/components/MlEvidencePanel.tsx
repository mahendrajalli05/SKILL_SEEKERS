"use client";

import { useState } from "react";

import { EvidenceCard } from "@/components/EvidenceCard";
import { createProjectMlEvidence } from "@/lib/api";
import type { DataMode, EvidenceObject } from "@/lib/types";

export function MlEvidencePanel({
  projectId,
  mode,
  items,
  onCreated,
}: {
  projectId: number;
  mode: DataMode;
  items: EvidenceObject[];
  onCreated?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const mlItems = items.filter(
    (item) => item.engine_name === "ml" || item.signal_type === "ML_ANOMALY_SIGNAL",
  );

  const generate = async () => {
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const created = await createProjectMlEvidence(projectId, { data_mode: mode });
      setStatus(`Stored ${created.evidence_id}. This is an ML anomaly signal, not fraud confirmation.`);
      onCreated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "ML evidence could not be stored.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-3 border border-[var(--line)] bg-white p-4">
      <div>
        <h3 className="font-semibold text-[var(--navy)]">ML Evidence</h3>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--violet)]">ML ANOMALY SIGNAL</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Identifies unusual patterns relative to the model's observed training distribution.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Unsupervised Isolation Forest anomaly signal for this stored project. Not a
          fraud probability, not fused into Investigation Priority, and not Evidence
          Confidence.
        </p>
      </div>
      <button className="svk-btn" type="button" disabled={busy} onClick={() => void generate()}>
        {busy ? "Generating…" : "Generate ML evidence"}
      </button>
      {status ? <p className="text-sm">{status}</p> : null}
      {error ? <p className="text-sm text-red-800">{error}</p> : null}
      {mlItems.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">No stored ML Evidence Objects for this view.</p>
      ) : (
        <div className="space-y-3">
          {mlItems.map((item) => (
            <EvidenceCard key={item.evidence_id} evidence={item} />
          ))}
        </div>
      )}
    </section>
  );
}
