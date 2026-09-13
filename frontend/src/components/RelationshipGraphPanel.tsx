"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { EvidenceCard } from "@/components/EvidenceCard";
import { RelationshipGraphView } from "@/components/RelationshipGraphView";
import { fetchGraph, fetchProject, fetchProjectEvidence } from "@/lib/api";
import {
  DEFAULT_VISIBLE_PEER_PROJECTS,
  DEFAULT_VISIBLE_SIMILAR,
  GRAPH_GOVERNANCE_NOTE,
  GRAPH_HYBRID_NOTICE,
  GRAPH_PRIORITY_NOTE,
  MAX_VISIBLE_PEER_PROJECTS,
  MAX_VISIBLE_SIMILAR,
  PEER_PAGE_SIZE,
  SIMILAR_PAGE_SIZE,
  buildVisibleNeighborhood,
  edgesForNode,
  findingKindLabel,
  graphResultDataMode,
  isGraphEvidence,
  nodeById,
  otherNodeId,
  relatedProjectId,
  relationshipDetailRows,
} from "@/lib/graphView";
import { withModePath } from "@/lib/display";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type {
  DataMode,
  EvidenceObject,
  GraphIntelligenceResponse,
  GraphRelationship,
  ProjectDetail,
} from "@/lib/types";

function engineMode(mode: DataMode): "real" | "hybrid-test" {
  return mode === "HYBRID" ? "hybrid-test" : "real";
}

function visibleGraphEvidence(
  items: EvidenceObject[],
  mode: DataMode,
  isSynthetic: boolean,
): EvidenceObject[] {
  const scoped =
    mode === "HYBRID" || isSynthetic ? items : items.filter((item) => item.data_mode === "REAL");
  return scoped.filter(isGraphEvidence);
}

export function RelationshipGraphPanel({
  projectId,
  mode,
  graph: graphProp,
  loading: loadingProp,
  error: errorProp,
  evidenceItems,
  schemeId,
  internalProjectId,
  isSynthetic = false,
}: {
  projectId: number;
  mode: DataMode;
  graph?: GraphIntelligenceResponse | null;
  loading?: boolean;
  error?: string | null;
  evidenceItems?: EvidenceObject[];
  schemeId?: string | null;
  internalProjectId?: string | null;
  isSynthetic?: boolean;
}) {
  const controlled = loadingProp !== undefined || graphProp !== undefined || errorProp !== undefined;
  const [fetchedGraph, setFetchedGraph] = useState<GraphIntelligenceResponse | null>(null);
  const [fetchedProject, setFetchedProject] = useState<ProjectDetail | null>(null);
  const [fetchedEvidence, setFetchedEvidence] = useState<EvidenceObject[]>([]);
  const [fetchLoading, setFetchLoading] = useState(!controlled);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [similarLimit, setSimilarLimit] = useState(DEFAULT_VISIBLE_SIMILAR);
  const [peerLimit, setPeerLimit] = useState(DEFAULT_VISIBLE_PEER_PROJECTS);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<{ rel: GraphRelationship; key: string } | null>(
    null,
  );

  const load = useCallback(async () => {
    if (controlled) {
      return;
    }
    setFetchLoading(true);
    setFetchError(null);
    try {
      const [graphBody, projectBody, evidenceBody] = await Promise.all([
        fetchGraph(projectId, engineMode(mode)),
        fetchProject(projectId, mode === "HYBRID" ? "hybrid" : "real"),
        fetchProjectEvidence(projectId),
      ]);
      setFetchedGraph(graphBody);
      setFetchedProject(projectBody);
      setFetchedEvidence(evidenceBody.items);
    } catch (err) {
      setFetchedGraph(null);
      setFetchError(err instanceof Error ? err.message : "Relationship graph could not be loaded.");
    } finally {
      setFetchLoading(false);
    }
  }, [controlled, mode, projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setSimilarLimit(DEFAULT_VISIBLE_SIMILAR);
    setPeerLimit(DEFAULT_VISIBLE_PEER_PROJECTS);
    setSelectedNodeId(null);
    setSelectedEdge(null);
  }, [projectId, mode, graphProp?.project_id]);

  const graph = controlled ? graphProp ?? null : fetchedGraph;
  const loading = controlled ? Boolean(loadingProp) : fetchLoading;
  const error = controlled ? errorProp ?? null : fetchError;
  const synthetic = isSynthetic || Boolean(fetchedProject?.is_synthetic);
  const displaySchemeId = schemeId ?? fetchedProject?.scheme_id ?? null;
  const displayInternalId =
    internalProjectId ?? fetchedProject?.internal_project_id ?? graph?.internal_project_id ?? null;
  const graphEvidence = visibleGraphEvidence(
    evidenceItems ?? fetchedEvidence,
    mode,
    synthetic,
  );
  const dataMode = graphResultDataMode(graph, synthetic);
  const neighborhood = useMemo(
    () => (graph ? buildVisibleNeighborhood(graph, similarLimit, peerLimit) : null),
    [graph, similarLimit, peerLimit],
  );

  const selectedNode = neighborhood
    ? nodeById(neighborhood.nodes, selectedNodeId)?.node
    : undefined;
  const nodeEdges =
    neighborhood && selectedNodeId ? edgesForNode(neighborhood.edges, selectedNodeId) : [];
  const detailRel = selectedEdge?.rel ?? nodeEdges[0] ?? null;
  const relatedId = detailRel ? relatedProjectId(detailRel, projectId) : selectedNode?.project_id;
  const relatedNode =
    neighborhood && detailRel && selectedNodeId
      ? nodeById(neighborhood.nodes, otherNodeId(detailRel, selectedNodeId))?.node
      : selectedNode;
  const evidenceAnchor = graphEvidence[0]?.evidence_id;
  const modePath = mode === "REAL" ? "REAL" : "HYBRID";
  const workspaceHref = withModePath(`/projects/${projectId}/investigate`, modePath);
  const evidenceHref = evidenceAnchor
    ? `${workspaceHref}#evidence-${evidenceAnchor}`
    : workspaceHref;
  const relatedHref =
    relatedId != null && relatedId !== projectId
      ? withModePath(`/projects/${relatedId}`, modePath)
      : null;

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="text-xl font-semibold text-[var(--navy)]">RELATIONSHIP GRAPH</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Ego-neighborhood from Relationship Graph V1. The frontend does not recalculate
          relationships.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">{GRAPH_PRIORITY_NOTE}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="border border-[var(--navy)] px-2 py-0.5 text-xs uppercase tracking-wide">
          {dataMode}
        </span>
        <StatusBadge value={dataMode} />
        {dataMode !== "REAL" ? (
          <span className="text-xs uppercase tracking-wide text-[var(--saffron)]">
            {GRAPH_HYBRID_NOTICE}
          </span>
        ) : (
          <span className="text-xs text-[var(--muted)]">
            REAL observed MPLADS fields and Overlap Intelligence SIMILAR_TO only.
          </span>
        )}
      </div>

      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Project / Scheme ID</dt>
          <dd>{displaySchemeId ?? "Unavailable in current public extract"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Internal Project ID</dt>
          <dd>{displayInternalId ?? "Unavailable in current public extract"}</dd>
        </div>
      </dl>

      {loading ? (
        <p className="text-sm text-[var(--muted)]">Loading relationship graph…</p>
      ) : null}
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}

      {graph && neighborhood ? (
        <>
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(16rem,0.8fr)]">
            <div>
              {neighborhood.isolated ? (
                <p className="mb-2 text-sm text-[var(--muted)]">
                  Isolated neighborhood: no connected entity or similar-project nodes were returned
                  for this work.
                </p>
              ) : null}
              <RelationshipGraphView
                neighborhood={neighborhood}
                selectedNodeId={selectedNodeId}
                selectedEdgeKey={selectedEdge?.key ?? null}
                onSelectNode={(nodeId) => {
                  setSelectedNodeId(nodeId);
                  setSelectedEdge(null);
                }}
                onSelectEdge={(rel, key) => {
                  setSelectedEdge({ rel, key });
                  setSelectedNodeId(rel.from_node_id === `PROJECT:${projectId}` ? rel.to_node_id : rel.from_node_id);
                }}
              />
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {neighborhood.hiddenSimilarCount > 0 ? (
                  <button
                    type="button"
                    className="border border-[var(--navy)] px-2 py-1"
                    onClick={() =>
                      setSimilarLimit((current) =>
                        Math.min(MAX_VISIBLE_SIMILAR, current + SIMILAR_PAGE_SIZE),
                      )
                    }
                  >
                    Show more similar projects ({neighborhood.hiddenSimilarCount} hidden)
                  </button>
                ) : null}
                {similarLimit > DEFAULT_VISIBLE_SIMILAR ? (
                  <button
                    type="button"
                    className="border border-[var(--line)] px-2 py-1"
                    onClick={() => setSimilarLimit(DEFAULT_VISIBLE_SIMILAR)}
                  >
                    Show fewer similar projects
                  </button>
                ) : null}
                {neighborhood.hiddenPeerCount > 0 ? (
                  <button
                    type="button"
                    className="border border-[var(--navy)] px-2 py-1"
                    onClick={() =>
                      setPeerLimit((current) =>
                        Math.min(MAX_VISIBLE_PEER_PROJECTS, current + PEER_PAGE_SIZE),
                      )
                    }
                  >
                    Expand cluster peers ({neighborhood.hiddenPeerCount} hidden)
                  </button>
                ) : null}
                {peerLimit > DEFAULT_VISIBLE_PEER_PROJECTS ? (
                  <button
                    type="button"
                    className="border border-[var(--line)] px-2 py-1"
                    onClick={() => setPeerLimit(DEFAULT_VISIBLE_PEER_PROJECTS)}
                  >
                    Collapse cluster peers
                  </button>
                ) : null}
              </div>
              <p className="mt-2 text-xs text-[var(--muted)]">
                Showing {neighborhood.nodes.length} nodes of this project-level neighborhood (not the
                full 56,138-project graph). Similar visible:{" "}
                {neighborhood.similarTotal - neighborhood.hiddenSimilarCount} / {neighborhood.similarTotal}.
              </p>
            </div>

            <aside className="space-y-3 border border-[var(--line)] p-3 text-sm">
              <h3 className="font-semibold text-[var(--navy)]">Relationship details</h3>
              {detailRel ? (
                <dl className="space-y-2">
                  {relationshipDetailRows(detailRel).map((row) => (
                    <div key={row.label}>
                      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">
                        {row.label}
                      </dt>
                      <dd>{row.value}</dd>
                    </div>
                  ))}
                  {relatedNode ? (
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">
                        Related project/node
                      </dt>
                      <dd>
                        {relatedNode.node_type}: {relatedNode.label}
                      </dd>
                    </div>
                  ) : null}
                </dl>
              ) : selectedNode ? (
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Node type</dt>
                    <dd>{selectedNode.node_type}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Label</dt>
                    <dd>{selectedNode.label}</dd>
                  </div>
                  {selectedNode.internal_project_id ? (
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">
                        Internal Project ID
                      </dt>
                      <dd>{selectedNode.internal_project_id}</dd>
                    </div>
                  ) : null}
                  <p className="text-[var(--muted)]">
                    Select a relationship line to inspect edge attributes returned by the API.
                  </p>
                </dl>
              ) : (
                <p className="text-[var(--muted)]">
                  Click a node or relationship to inspect API attributes. Relationships are not invented
                  in the browser.
                </p>
              )}
            </aside>
          </div>

          <section className="space-y-2">
            <h3 className="font-semibold text-[var(--navy)]">Graph finding</h3>
            <p className="text-sm font-medium">{findingKindLabel(graph.finding_kind)}</p>
            {(graph.graph_evidence ?? graph.graph_findings[0]) ? (
              <>
                <p className="text-sm">{(graph.graph_evidence ?? graph.graph_findings[0])?.summary}</p>
                <p className="text-sm text-[var(--muted)]">
                  {(graph.graph_evidence ?? graph.graph_findings[0])?.details}
                </p>
              </>
            ) : null}
            <p className="text-sm text-[var(--muted)]">{graph.explanation}</p>
            {graph.finding_kind === "INSUFFICIENT_EVIDENCE" ? (
              <p className="text-sm text-[var(--muted)]">
                Insufficient evidence: usable entity fields and similar works were not available for
                this neighborhood.
              </p>
            ) : null}
          </section>

          <section className="space-y-2">
            <h3 className="font-semibold text-[var(--navy)]">Related projects</h3>
            {neighborhood.similarTotal === 0 ? (
              <p className="text-sm text-[var(--muted)]">No SIMILAR_TO projects in this neighborhood.</p>
            ) : (
              <ul className="divide-y divide-[var(--line)] text-sm">
                {(graph.relationships ?? [])
                  .filter((rel) => rel.edge_type === "SIMILAR_TO")
                  .map((rel) => {
                    const linkedId = relatedProjectId(rel, projectId);
                    if (linkedId == null) {
                      return null;
                    }
                    const node = (graph.connected_nodes ?? []).find(
                      (item) => item.project_id === linkedId,
                    );
                    return (
                      <li key={`${rel.from_node_id}-${rel.to_node_id}`} className="py-2">
                        <Link
                          className="font-medium text-[var(--navy)]"
                          href={withModePath(`/projects/${linkedId}`, modePath)}
                        >
                          {node?.internal_project_id ?? `Project ${linkedId}`}
                        </Link>
                        <p className="text-[var(--muted)]">
                          {rel.edge_type} · strength {rel.strength.toFixed(2)}
                          {rel.same_constituency != null
                            ? ` · same constituency: ${rel.same_constituency ? "YES" : "NO"}`
                            : ""}
                          {rel.date_gap_days != null
                            ? ` · recommendation gap: ${rel.date_gap_days} days`
                            : ""}
                        </p>
                      </li>
                    );
                  })}
              </ul>
            )}
          </section>

          <section className="space-y-2">
            <h3 className="font-semibold text-[var(--navy)]">Evidence</h3>
            <p className="text-sm">
              {(graph.graph_evidence ?? graph.graph_findings[0])?.summary ?? graph.explanation}
            </p>
            {graphEvidence.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">
                No stored Graph Evidence Objects for this view. The finding above is the graph API
                evidence payload.
              </p>
            ) : (
              graphEvidence.map((item) => (
                <div key={item.evidence_id}>
                  <EvidenceCard evidence={item} />
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Source: {item.source_type}. Provenance: {item.provenance?.notes ?? "Unavailable"}.
                  </p>
                </div>
              ))
            )}
          </section>

          <div className="flex flex-wrap gap-2">
            {relatedHref ? (
              <Link
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)]"
                href={relatedHref}
              >
                Open related project
              </Link>
            ) : (
              <span className="border border-[var(--line)] px-3 py-1.5 text-sm text-[var(--muted)]">
                Open related project
              </span>
            )}
            <Link
              className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)]"
              href={evidenceHref}
            >
              Open Evidence
            </Link>
            <Link
              className="bg-[var(--navy)] px-3 py-1.5 text-sm text-white"
              href={workspaceHref}
            >
              Return to Investigation Workspace
            </Link>
          </div>

          {graph.gps_used ? (
            <p className="text-xs text-[var(--saffron)]">
              GPS was used only inside Overlap SIMILAR_TO scoring. GPS is not a REAL graph node or
              edge type.
            </p>
          ) : null}
          <p className="text-xs text-[var(--muted)]">{GRAPH_GOVERNANCE_NOTE}</p>
        </>
      ) : null}
    </section>
  );
}
