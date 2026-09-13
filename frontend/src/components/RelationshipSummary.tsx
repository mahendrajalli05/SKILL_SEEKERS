import Link from "next/link";

import type { GraphIntelligenceResponse } from "@/lib/types";
import { findingKindLabel, graphResultDataMode } from "@/lib/graphView";

export function RelationshipSummary({
  graph,
  loading,
  error,
  openHref,
}: {
  graph?: GraphIntelligenceResponse | null;
  loading?: boolean;
  error?: string | null;
  openHref?: string;
}) {
  const connectedNodes = graph?.connected_nodes?.length ?? 0;
  const similarProjects = graph?.stats.similar_project_count ?? 0;
  const dataMode = graph ? graphResultDataMode(graph) : null;

  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">Relationship summary</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Compact neighborhood counts from Relationship Graph V1. This summary does not
        recalculate relationships and is not fused into Investigation Priority.
      </p>
      {loading ? (
        <p className="mt-3 text-sm text-[var(--muted)]">Loading relationship neighborhood…</p>
      ) : null}
      {error ? <p className="mt-3 text-sm text-[var(--saffron)]">{error}</p> : null}
      {graph ? (
        <>
          {dataMode && dataMode !== "REAL" ? (
            <p className="mt-3 text-xs uppercase tracking-wide text-[var(--saffron)]">
              {dataMode} — not official MPLADS graph findings
            </p>
          ) : (
            <p className="mt-3 text-xs uppercase tracking-wide text-[var(--muted)]">REAL</p>
          )}
          <dl className="mt-4 grid gap-3 sm:grid-cols-3">
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Connected nodes</dt>
              <dd>{connectedNodes}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Similar projects</dt>
              <dd>{similarProjects}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Graph finding</dt>
              <dd>{findingKindLabel(graph.finding_kind)}</dd>
            </div>
          </dl>
          {openHref ? (
            <Link
              href={openHref}
              className="mt-4 inline-block bg-[var(--navy)] px-3 py-1.5 text-sm text-white"
            >
              Open Relationship Graph
            </Link>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
