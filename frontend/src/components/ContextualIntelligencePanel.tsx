"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { fetchProjectContext, refreshProjectContext } from "@/lib/api";
import type { DataMode, ProjectContextObservation, ProjectContextResponse } from "@/lib/types";

function kindLabel(kind: string) {
  if (kind === "PROJECT_SPECIFIC_FACT") {
    return "PROJECT OBSERVATION";
  }
  if (kind === "OBSERVED_EXTERNAL_INDICATOR") {
    return "EXTERNAL CONTEXT";
  }
  if (kind === "DERIVED_CONTEXT") {
    return "DERIVED COMPARISON";
  }
  return kind;
}

/** Stable list key: observations have no id; indicator is not unique across sources. */
export function observationKey(item: ProjectContextObservation, index?: number): string {
  const composite = [
    item.indicator,
    item.source_id ?? "no_source",
    item.source_name ?? "no_source_name",
    item.context_kind,
    item.status,
    item.failure_code ?? "",
    item.geographic_level ?? "",
    item.geo_key ?? "",
    item.reference_year == null ? "" : String(item.reference_year),
    item.reference_date ?? "",
    item.dataset_version ?? "",
    item.data_mode,
    item.quality,
  ].join("|");
  return index == null ? composite : `${composite}#${index}`;
}

function ObservationBlock({ item }: { item: ProjectContextObservation }) {
  return (
    <div className="border border-[var(--line)] p-3">
      <p className="text-xs uppercase tracking-[0.12em] text-[var(--muted)]">{kindLabel(item.context_kind)}</p>
      <dl className="mt-2">
        <FieldRow label="Indicator" value={item.indicator} />
        <FieldRow label="Status" value={item.status} />
        <FieldRow label="Value" value={item.value == null ? "UNAVAILABLE / INCONCLUSIVE" : String(item.value)} />
        <FieldRow label="Unit" value={item.unit} />
        <FieldRow label="Source" value={item.source_name} />
        <FieldRow label="Publisher" value={item.publisher} />
        <FieldRow label="Reference period" value={item.reference_year ?? item.reference_date} />
        <FieldRow label="Geographic level" value={item.geographic_level} />
        <FieldRow label="Data mode" value={item.data_mode} />
        <FieldRow label="Confidence/quality" value={`${item.confidence} · ${item.quality}`} />
      </dl>
      <p className="mt-2 text-sm">{item.notes}</p>
      {item.limitations[0] ? (
        <p className="mt-1 text-xs text-[var(--muted)]">Limitations: {item.limitations[0]}</p>
      ) : null}
    </div>
  );
}

export function ContextualIntelligencePanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [data, setData] = useState<ProjectContextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await fetchProjectContext(projectId, mode);
      setData(body);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Contextual intelligence could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = async () => {
    setBusy(true);
    try {
      const body = await refreshProjectContext(projectId, mode);
      setData(body);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Contextual refresh failed.");
    } finally {
      setBusy(false);
    }
  };

  if (error) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Contextual Intelligence</h2>
        <p className="mt-2 text-sm text-[var(--saffron)]">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Contextual Intelligence</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Loading external contextual indicators…</p>
      </section>
    );
  }

  const cost = data.observations.filter((item) =>
    item.indicator.includes("cost") ||
    item.indicator.includes("allocation") ||
    item.indicator.includes("expenditure") ||
    item.indicator.includes("reference"),
  );
  const need = data.observations.filter((item) => item.indicator.includes("population"));
  const infra = data.observations.filter(
    (item) =>
      item.indicator.includes("infrastructure") ||
      item.indicator.includes("electricity") ||
      item.indicator.includes("water") ||
      item.indicator.includes("sanitation") ||
      item.indicator.includes("district"),
  );

  return (
    <section id="contextual-intelligence" className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">Contextual Intelligence</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Adds verified external public indicators without treating them as project-specific facts.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">{data.governance_note}</p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Cost V1.1, Need & Impact formula, and Risk Fusion are unchanged. External context is not a
          project-specific fact. Regional statistic; not a project-specific beneficiary count.
        </p>
      </div>
      <button className="svk-btn" type="button" disabled={busy} onClick={() => void refresh()}>
        {busy ? "Refreshing…" : "Refresh contextual snapshot"}
      </button>
      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Reference cost context</h3>
        <div className="mt-2 space-y-2">
          {cost.map((item, index) => (
            <ObservationBlock key={observationKey(item, index)} item={item} />
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Development need context</h3>
        <div className="mt-2 space-y-2">
          {need.map((item, index) => (
            <ObservationBlock key={observationKey(item, index)} item={item} />
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Infrastructure context</h3>
        <div className="mt-2 space-y-2">
          {infra.map((item, index) => (
            <ObservationBlock key={observationKey(item, index)} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}
