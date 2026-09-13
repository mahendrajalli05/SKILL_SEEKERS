import type {
  DataMode,
  GraphIntelligenceResponse,
  GraphNode,
  GraphRelationship,
} from "@/lib/types";

export const DEFAULT_VISIBLE_SIMILAR = 12;
export const SIMILAR_PAGE_SIZE = 12;
export const MAX_VISIBLE_SIMILAR = 36;
export const DEFAULT_VISIBLE_PEER_PROJECTS = 0;
export const PEER_PAGE_SIZE = 8;
export const MAX_VISIBLE_PEER_PROJECTS = 16;

export const GRAPH_VIEWBOX_WIDTH = 800;
export const GRAPH_VIEWBOX_HEIGHT = 560;
export const GRAPH_CENTER_X = 400;
export const GRAPH_CENTER_Y = 280;

export const GRAPH_PRIORITY_NOTE =
  "Relationship Graph Visualization does not modify Investigation Priority. Risk Fusion V1.1 is unchanged.";

export const GRAPH_GOVERNANCE_NOTE =
  "Relationship findings are investigation aids. They are not a legal finding. AI recommends. Authorized officers decide.";

export const GRAPH_HYBRID_NOTICE =
  "HYBRID / SYNTHETIC graph relationships are prototype evaluation output and are not official MPLADS findings.";

export const GRAPH_FINDING_KINDS = [
  "NORMAL_CONNECTIVITY",
  "HIGH_CONNECTIVITY",
  "POTENTIAL_PATTERN_OF_INTEREST",
  "INSUFFICIENT_EVIDENCE",
] as const;

const ENTITY_ORDER = ["MP", "CONSTITUENCY", "CATEGORY", "IDA", "STATE"] as const;

export interface PlacedNode {
  node: GraphNode;
  x: number;
  y: number;
  ring: "center" | "entity" | "similar" | "peer";
}

export interface VisibleNeighborhood {
  nodes: PlacedNode[];
  edges: GraphRelationship[];
  similarTotal: number;
  peerTotal: number;
  hiddenSimilarCount: number;
  hiddenPeerCount: number;
  entityCount: number;
  isolated: boolean;
}

export function graphResultDataMode(
  graph: GraphIntelligenceResponse | null | undefined,
  isSynthetic = false,
): DataMode {
  if (isSynthetic) {
    return "SYNTHETIC";
  }
  const mode = (graph?.graph_mode ?? "").toUpperCase();
  const dataset = (graph?.dataset_type ?? "").toUpperCase();
  if (dataset === "SYNTHETIC" || mode.includes("SYNTHETIC")) {
    return "SYNTHETIC";
  }
  if (dataset === "HYBRID" || mode.includes("HYBRID")) {
    return "HYBRID";
  }
  return "REAL";
}

export function findingKindLabel(kind: string | null | undefined): string {
  return (kind ?? "").trim() || "INSUFFICIENT_EVIDENCE";
}

export function yesNo(value: boolean | null | undefined): string | null {
  if (value == null) {
    return null;
  }
  return value ? "YES" : "NO";
}

export function formatStrength(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "Unavailable";
  }
  return value.toFixed(2);
}

export function similarityDisplay(rel: GraphRelationship): string | null {
  if (rel.strength != null) {
    return formatStrength(rel.strength);
  }
  if (rel.similarity_score == null) {
    return null;
  }
  const score = rel.similarity_score > 1 ? rel.similarity_score / 100 : rel.similarity_score;
  return formatStrength(score);
}

export function relatedProjectId(
  rel: GraphRelationship,
  subjectProjectId: number,
): number | null {
  if (rel.from_project_id === subjectProjectId) {
    return rel.to_project_id ?? null;
  }
  if (rel.to_project_id === subjectProjectId) {
    return rel.from_project_id ?? null;
  }
  return null;
}

export function involvesSubject(
  rel: GraphRelationship,
  subjectNodeId: string,
  subjectProjectId: number,
): boolean {
  return (
    rel.from_node_id === subjectNodeId ||
    rel.to_node_id === subjectNodeId ||
    rel.from_project_id === subjectProjectId ||
    rel.to_project_id === subjectProjectId
  );
}

export function otherNodeId(rel: GraphRelationship, nodeId: string): string {
  return rel.from_node_id === nodeId ? rel.to_node_id : rel.from_node_id;
}

export function truncateLabel(value: string, max = 22): string {
  const text = value.trim();
  if (text.length <= max) {
    return text;
  }
  return `${text.slice(0, max - 1)}…`;
}

export function relationshipDetailRows(rel: GraphRelationship): Array<{ label: string; value: string }> {
  const rows: Array<{ label: string; value: string }> = [
    { label: "Edge type", value: rel.edge_type },
    { label: "Related node", value: `${rel.from_node_id} → ${rel.to_node_id}` },
    { label: "Relationship strength", value: formatStrength(rel.strength) },
  ];
  const similarity = similarityDisplay(rel);
  if (similarity != null && rel.edge_type === "SIMILAR_TO") {
    rows.push({ label: "Similarity", value: similarity });
  }
  const constituency = yesNo(rel.same_constituency);
  if (constituency) {
    rows.push({ label: "Same constituency", value: constituency });
  }
  const category = yesNo(rel.same_category);
  if (category) {
    rows.push({ label: "Same category", value: category });
  }
  const ida = yesNo(rel.same_ida);
  if (ida) {
    rows.push({ label: "Same IDA", value: ida });
  }
  const allocation = yesNo(rel.similar_allocation);
  if (allocation) {
    rows.push({ label: "Similar allocation", value: allocation });
  }
  const closeDates = yesNo(rel.close_recommendation_dates);
  if (closeDates) {
    rows.push({ label: "Close recommendation dates", value: closeDates });
  }
  if (rel.date_gap_days != null) {
    rows.push({ label: "Recommendation gap", value: `${rel.date_gap_days} days` });
  }
  if (rel.semantic_similarity != null) {
    rows.push({
      label: "Semantic similarity",
      value: formatStrength(
        rel.semantic_similarity > 1 ? rel.semantic_similarity / 100 : rel.semantic_similarity,
      ),
    });
  }
  if (rel.overlap_outcome) {
    rows.push({ label: "Overlap outcome", value: rel.overlap_outcome });
  }
  if (rel.gps_distance_m != null) {
    rows.push({ label: "GPS distance (HYBRID)", value: `${Math.round(rel.gps_distance_m)} m` });
  }
  return rows;
}

function subjectNode(graph: GraphIntelligenceResponse): GraphNode {
  if (graph.project_node) {
    return graph.project_node;
  }
  return {
    node_id: `PROJECT:${graph.project_id}`,
    node_type: "PROJECT",
    label: graph.internal_project_id ?? `Project ${graph.project_id}`,
    project_id: graph.project_id,
    internal_project_id: graph.internal_project_id ?? null,
    attributes: {},
  };
}

function similarStrength(
  node: GraphNode,
  relationships: GraphRelationship[],
  subjectNodeId: string,
  subjectProjectId: number,
): number {
  let best = 0;
  for (const rel of relationships) {
    if (rel.edge_type !== "SIMILAR_TO") {
      continue;
    }
    if (!involvesSubject(rel, subjectNodeId, subjectProjectId)) {
      continue;
    }
    const other = otherNodeId(rel, subjectNodeId);
    const matchesNode =
      other === node.node_id ||
      rel.from_project_id === node.project_id ||
      rel.to_project_id === node.project_id;
    if (matchesNode) {
      best = Math.max(best, rel.strength);
    }
  }
  return best;
}

function polar(count: number, index: number, radius: number, start = -Math.PI / 2): { x: number; y: number } {
  const angle = start + (index * 2 * Math.PI) / Math.max(count, 1);
  return {
    x: GRAPH_CENTER_X + radius * Math.cos(angle),
    y: GRAPH_CENTER_Y + radius * Math.sin(angle),
  };
}

export function buildVisibleNeighborhood(
  graph: GraphIntelligenceResponse,
  similarLimit = DEFAULT_VISIBLE_SIMILAR,
  peerLimit = DEFAULT_VISIBLE_PEER_PROJECTS,
): VisibleNeighborhood {
  const center = subjectNode(graph);
  const connected = graph.connected_nodes ?? [];
  const relationships = graph.relationships ?? [];
  const similarIds = new Set<string>();
  for (const rel of relationships) {
    if (rel.edge_type !== "SIMILAR_TO") {
      continue;
    }
    if (!involvesSubject(rel, center.node_id, graph.project_id)) {
      continue;
    }
    similarIds.add(otherNodeId(rel, center.node_id));
    if (rel.from_project_id != null && rel.from_project_id !== graph.project_id) {
      similarIds.add(`PROJECT:${rel.from_project_id}`);
    }
    if (rel.to_project_id != null && rel.to_project_id !== graph.project_id) {
      similarIds.add(`PROJECT:${rel.to_project_id}`);
    }
  }

  const entityNodes = connected
    .filter((node) => node.node_type !== "PROJECT")
    .slice()
    .sort((a, b) => {
      const ai = ENTITY_ORDER.indexOf(a.node_type as (typeof ENTITY_ORDER)[number]);
      const bi = ENTITY_ORDER.indexOf(b.node_type as (typeof ENTITY_ORDER)[number]);
      const ao = ai === -1 ? 99 : ai;
      const bo = bi === -1 ? 99 : bi;
      if (ao !== bo) {
        return ao - bo;
      }
      return a.node_id.localeCompare(b.node_id);
    });

  const similarNodes = connected
    .filter((node) => node.node_type === "PROJECT" && similarIds.has(node.node_id))
    .slice()
    .sort((a, b) => {
      const strength =
        similarStrength(b, relationships, center.node_id, graph.project_id) -
        similarStrength(a, relationships, center.node_id, graph.project_id);
      if (strength !== 0) {
        return strength;
      }
      return (a.project_id ?? 0) - (b.project_id ?? 0);
    });

  const peerNodes = connected
    .filter(
      (node) =>
        node.node_type === "PROJECT" &&
        node.node_id !== center.node_id &&
        !similarIds.has(node.node_id),
    )
    .slice()
    .sort((a, b) => (a.project_id ?? 0) - (b.project_id ?? 0));

  const cappedSimilar = Math.min(Math.max(similarLimit, 0), MAX_VISIBLE_SIMILAR);
  const cappedPeers = Math.min(Math.max(peerLimit, 0), MAX_VISIBLE_PEER_PROJECTS);
  const visibleSimilar = similarNodes.slice(0, cappedSimilar);
  const visiblePeers = peerNodes.slice(0, cappedPeers);

  const placed: PlacedNode[] = [{ node: center, x: GRAPH_CENTER_X, y: GRAPH_CENTER_Y, ring: "center" }];

  entityNodes.forEach((node, index) => {
    const point = polar(entityNodes.length, index, 145);
    placed.push({ node, x: point.x, y: point.y, ring: "entity" });
  });
  visibleSimilar.forEach((node, index) => {
    const point = polar(visibleSimilar.length, index, 250, -Math.PI / 2 + 0.2);
    placed.push({ node, x: point.x, y: point.y, ring: "similar" });
  });
  visiblePeers.forEach((node, index) => {
    const point = polar(visiblePeers.length, index, 205, Math.PI / 6);
    placed.push({ node, x: point.x, y: point.y, ring: "peer" });
  });

  const visibleIds = new Set(placed.map((item) => item.node.node_id));
  const edges = relationships.filter(
    (rel) => visibleIds.has(rel.from_node_id) && visibleIds.has(rel.to_node_id),
  );

  return {
    nodes: placed,
    edges,
    similarTotal: similarNodes.length,
    peerTotal: peerNodes.length,
    hiddenSimilarCount: Math.max(0, similarNodes.length - visibleSimilar.length),
    hiddenPeerCount: Math.max(0, peerNodes.length - visiblePeers.length),
    entityCount: entityNodes.length,
    isolated: connected.length === 0 && relationships.length === 0,
  };
}

export function nodeById(nodes: PlacedNode[], nodeId: string | null | undefined): PlacedNode | undefined {
  if (!nodeId) {
    return undefined;
  }
  return nodes.find((item) => item.node.node_id === nodeId);
}

export function edgesForNode(edges: GraphRelationship[], nodeId: string): GraphRelationship[] {
  return edges.filter((rel) => rel.from_node_id === nodeId || rel.to_node_id === nodeId);
}

export function isGraphEvidence(item: { engine_name?: string; signal_type?: string }): boolean {
  const engine = (item.engine_name ?? "").toLowerCase();
  const signal = (item.signal_type ?? "").toLowerCase();
  return engine === "graph" || signal === "relationship_graph";
}
