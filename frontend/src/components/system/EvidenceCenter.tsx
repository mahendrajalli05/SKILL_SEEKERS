"use client";

import { useMemo, useState } from "react";

import { EvidenceCard } from "@/components/EvidenceCard";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { EvidenceObject } from "@/lib/types";

const FILTERS = [
  "ALL",
  "COST",
  "TIME",
  "OVERLAP",
  "COMPLIANCE",
  "DOCUMENT",
  "IMAGE",
  "FORENSICS",
  "GEO",
  "SATELLITE",
  "CITIZEN",
  "ML",
  "MILESTONE",
  "PCE",
  "CONTEXT",
] as const;

function matchesFilter(item: EvidenceObject, filter: string) {
  if (filter === "ALL") return true;
  const hay = `${item.engine_name} ${item.signal_type} ${item.finding}`.toUpperCase();
  if (filter === "GEO") return hay.includes("GEO") || hay.includes("LOCATION");
  if (filter === "PCE") return hay.includes("PCE") || hay.includes("PLAN") || hay.includes("CLAIM");
  return hay.includes(filter);
}

function kindLabel(item: EvidenceObject) {
  if (item.engine_name === "ml" || item.signal_type === "ML_ANOMALY_SIGNAL") return "SCORE";
  if (item.disposition) return "DERIVED FINDING";
  return "OBSERVATION";
}

export function EvidenceCenter({
  items,
  loading,
  error,
}: {
  items: EvidenceObject[];
  loading?: boolean;
  error?: string | null;
}) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("ALL");
  const visible = useMemo(() => items.filter((item) => matchesFilter(item, filter)), [items, filter]);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((item) => (
          <button
            key={item}
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold tracking-[0.08em] ${
              filter === item ? "bg-[var(--navy-fill)] text-white" : "border border-[var(--line)] bg-white"
            }`}
            onClick={() => setFilter(item)}
          >
            {item}
          </button>
        ))}
      </div>
      {loading ? <PageState kind="loading" message="Loading evidence…" compact /> : null}
      {error ? <PageState kind="error" message={error} compact /> : null}
      {visible.length === 0 && !loading ? (
        <PageState kind="empty" message="No evidence objects match this filter." />
      ) : (
        <div className="space-y-3">
          {visible.map((item) => (
            <article key={item.evidence_id} className="svk-panel p-4">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge label={kindLabel(item)} />
                <StatusBadge value={item.status} />
                <StatusBadge value={String(item.data_mode)} />
                <span className="text-xs uppercase tracking-wide text-[var(--muted)]">{item.engine_name}</span>
              </div>
              <p className="mt-2 text-sm">{item.explanation}</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Source: {item.source_type || "unavailable"} · Confidence:{" "}
                {item.confidence == null ? "unavailable" : `${Math.round(item.confidence * 100)} / 100`} ·{" "}
                {item.created_at ?? "timestamp unavailable"}
                {item.score != null ? ` · Score ${item.score}` : ""}
              </p>
              <details className="mt-2">
                <summary className="cursor-pointer text-sm text-[var(--navy)]">Expand details</summary>
                <div className="mt-2">
                  <EvidenceCard evidence={item} />
                </div>
              </details>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
