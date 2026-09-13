"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { fetchCitizenSummary } from "@/lib/api";
import type { CitizenSummary, DataMode } from "@/lib/types";

export function CitizenEvidenceSummary({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [data, setData] = useState<CitizenSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const body = await fetchCitizenSummary(projectId, mode);
      setData(body);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Citizen evidence could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Citizen Evidence</h2>
        <p className="mt-2 text-sm text-[var(--saffron)]">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Citizen Evidence</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Loading citizen evidence…</p>
      </section>
    );
  }

  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">Citizen Evidence</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">{data.governance_note}</p>
      {data.synthetic_badge ? (
        <p className="mt-2 text-xs uppercase tracking-wide text-[var(--saffron)]">{data.synthetic_badge}</p>
      ) : null}
      <dl className="mt-3">
        <FieldRow label="Citizen reports" value={String(data.total_submissions)} />
        <FieldRow label="Verified reports" value={String(data.verified_location_submissions)} />
        <FieldRow label="Rejected reports" value={String(data.rejected_submissions)} />
        <FieldRow
          label="Average satisfaction"
          value={data.average_satisfaction == null ? "unavailable" : String(data.average_satisfaction)}
        />
        <FieldRow
          label="Top recurring issues"
          value={
            data.recurring_issue_categories.length
              ? data.recurring_issue_categories.map((item) => `${item.label} (${item.count})`).join(", ")
              : "none"
          }
        />
        <FieldRow label="Citizen evidence confidence" value={String(data.citizen_evidence_confidence)} />
        <FieldRow label="Sample" value={data.sample_size_status} />
      </dl>
      <p className="mt-3 text-sm">{data.explanation}</p>
      <p className="mt-2 text-xs text-[var(--muted)]">
        Investigation Priority is not changed by citizen evidence in V1. {data.privacy_note}
      </p>
    </section>
  );
}
