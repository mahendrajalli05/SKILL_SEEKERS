import type {
  EvidenceObject,
  GraphIntelligenceResponse,
  GraphNode,
  GraphRelationship,
  ProjectDetail,
} from "@/lib/types";
import { SCHEME_ID_NOTE } from "@/lib/display";

function entity(
  type: GraphNode["node_type"],
  label: string,
): GraphNode {
  return {
    node_id: `${type}:${label.toLowerCase()}`,
    node_type: type,
    label,
    project_id: null,
    internal_project_id: null,
    attributes: {},
  };
}

function projectNode(
  id: number,
  label: string,
  internal = `internal:${id}`,
): GraphNode {
  return {
    node_id: `PROJECT:${id}`,
    node_type: "PROJECT",
    label,
    project_id: id,
    internal_project_id: internal,
    attributes: {},
  };
}

function similarEdge(
  fromId: number,
  toId: number,
  strength: number,
  extras: Partial<GraphRelationship> = {},
): GraphRelationship {
  return {
    from_node_id: `PROJECT:${fromId}`,
    to_node_id: `PROJECT:${toId}`,
    edge_type: "SIMILAR_TO",
    strength,
    from_project_id: fromId,
    to_project_id: toId,
    same_constituency: true,
    same_category: true,
    same_ida: true,
    similar_allocation: true,
    close_recommendation_dates: true,
    semantic_similarity: strength,
    similarity_score: Math.round(strength * 100),
    date_gap_days: 18,
    overlap_outcome: "POTENTIAL_DUPLICATE",
    gps_distance_m: null,
    ...extras,
  };
}

export function sampleProject(overrides: Partial<ProjectDetail> = {}): ProjectDetail {
  return {
    id: 232,
    scheme_id: "SVK-AP-000232",
    scheme_id_note: SCHEME_ID_NOTE,
    internal_project_id: "internal:232",
    internal_id_kind: "internal_surrogate_hash",
    internal_id_scheme: "sarvsakshi_internal_work_v1",
    source_dataset: "github_vonter_india-mplads-works_MPLADS.csv",
    mp_name: "Test MP",
    work_description: "Construction of roads in Hindupur",
    category: "Roads",
    state: "Andhra Pradesh",
    constituency: "HINDUPUR",
    ida: "Hindupur_IDA",
    city: null,
    ward: null,
    block: null,
    village: null,
    recommended_date: "2023-06-01",
    allocation_amount: 500000,
    ida_approval: null,
    status: "Ongoing",
    house: "Lok Sabha",
    lifecycle_stage: "ONGOING",
    is_synthetic: false,
    synthetic_label: null,
    has_hybrid_enrichment: false,
    hybrid_notice: null,
    amount_unit_note: "Source amount unit is unspecified.",
    unavailable_fields: [],
    snapshot_source_url: "https://example.invalid/extract",
    snapshot_extracted_at: "2026-09-09",
    snapshot_download_date: "2026-09-09",
    snapshot_publisher: "test",
    snapshot_notes: "Observed extract.",
    snapshot_original_filename: "mplads_works_cleaned.csv",
    data_mode_default: "HYBRID",
    data_mode: "REAL",
    synthetic_enrichment: null,
    ...overrides,
  };
}

export function graphEvidenceObject(
  overrides: Partial<EvidenceObject> = {},
): EvidenceObject {
  return {
    evidence_id: "ev:graph:232:relationship_graph:REAL:abc",
    project_id: 232,
    signal_type: "relationship_graph",
    finding:
      "29 highly similar works in the same constituency, with 29 sharing the same IDA and 29 recommended within 60 days.",
    severity: "watch",
    score: 64,
    confidence: 0.64,
    source_type: "mplads_project_record",
    source_ids: ["internal:232"],
    evidence_facts: [],
    explanation:
      "Potential Pattern of Interest from observed entity links and Overlap Intelligence similarity.",
    engine_name: "graph",
    engine_version: "relationship-graph-v1",
    created_at: "2026-09-10T00:00:00Z",
    data_mode: "REAL",
    provenance: {
      data_mode: "REAL",
      source_type: "mplads_project_record",
      notes: "real MPLADS project records from the cleaned work-level extract.",
    },
    disposition: "WHY_FLAGGED",
    status: "mismatch",
    comparables: [],
    ...overrides,
  };
}

export function sampleGraph(
  overrides: Partial<GraphIntelligenceResponse> = {},
  options: { similarCount?: number; peerCount?: number } = {},
): GraphIntelligenceResponse {
  const similarCount = options.similarCount ?? 3;
  const peerCount = options.peerCount ?? 0;
  const similarNodes = Array.from({ length: similarCount }, (_, index) =>
    projectNode(3700 + index, `Similar road work ${index + 1}`, `internal:${3700 + index}`),
  );
  const peerNodes = Array.from({ length: peerCount }, (_, index) =>
    projectNode(5000 + index, `Cluster peer ${index + 1}`, `internal:${5000 + index}`),
  );
  const entities = [
    entity("MP", "Test MP"),
    entity("CONSTITUENCY", "HINDUPUR"),
    entity("CATEGORY", "Roads"),
    entity("IDA", "Hindupur_IDA"),
    entity("STATE", "Andhra Pradesh"),
  ];
  const relationships: GraphRelationship[] = [
    {
      from_node_id: "PROJECT:232",
      to_node_id: "MP:test mp",
      edge_type: "RECOMMENDED_BY",
      strength: 1,
      from_project_id: 232,
      to_project_id: null,
      same_constituency: null,
      same_category: null,
      same_ida: null,
      similar_allocation: null,
      close_recommendation_dates: null,
      semantic_similarity: null,
      similarity_score: null,
      date_gap_days: null,
      overlap_outcome: null,
      gps_distance_m: null,
    },
    {
      from_node_id: "PROJECT:232",
      to_node_id: "CONSTITUENCY:hindupur",
      edge_type: "LOCATED_IN_CONSTITUENCY",
      strength: 1,
      from_project_id: 232,
      to_project_id: null,
      same_constituency: null,
      same_category: null,
      same_ida: null,
      similar_allocation: null,
      close_recommendation_dates: null,
      semantic_similarity: null,
      similarity_score: null,
      date_gap_days: null,
      overlap_outcome: null,
      gps_distance_m: null,
    },
    {
      from_node_id: "PROJECT:232",
      to_node_id: "CATEGORY:roads",
      edge_type: "HAS_CATEGORY",
      strength: 1,
      from_project_id: 232,
      to_project_id: null,
      same_constituency: null,
      same_category: null,
      same_ida: null,
      similar_allocation: null,
      close_recommendation_dates: null,
      semantic_similarity: null,
      similarity_score: null,
      date_gap_days: null,
      overlap_outcome: null,
      gps_distance_m: null,
    },
    {
      from_node_id: "PROJECT:232",
      to_node_id: "IDA:hindupur_ida",
      edge_type: "ASSOCIATED_WITH_IDA",
      strength: 1,
      from_project_id: 232,
      to_project_id: null,
      same_constituency: null,
      same_category: null,
      same_ida: null,
      similar_allocation: null,
      close_recommendation_dates: null,
      semantic_similarity: null,
      similarity_score: null,
      date_gap_days: null,
      overlap_outcome: null,
      gps_distance_m: null,
    },
    {
      from_node_id: "PROJECT:232",
      to_node_id: "STATE:andhra pradesh",
      edge_type: "IN_STATE",
      strength: 1,
      from_project_id: 232,
      to_project_id: null,
      same_constituency: null,
      same_category: null,
      same_ida: null,
      similar_allocation: null,
      close_recommendation_dates: null,
      semantic_similarity: null,
      similarity_score: null,
      date_gap_days: null,
      overlap_outcome: null,
      gps_distance_m: null,
    },
    ...similarNodes.map((node, index) =>
      similarEdge(232, node.project_id ?? 3700 + index, 0.91 - index * 0.01),
    ),
  ];
  const finding = {
    kind: "POTENTIAL_PATTERN_OF_INTEREST",
    summary:
      "29 highly similar works in the same constituency, with 29 sharing the same IDA and 29 recommended within 60 days.",
    details:
      "Multiple independent relationship signals among similar peers. This is not a legal finding.",
    score: 64,
    confidence: 64,
    independent_signal_count: 5,
    independent_signals: [
      "semantic_similarity",
      "same_constituency",
      "same_category",
      "same_ida",
      "close_recommendation_dates",
    ],
  };
  return {
    project_id: 232,
    internal_project_id: "internal:232",
    engine: "graph",
    engine_version: "relationship-graph-v1",
    evidence_type: "relationship_graph",
    dataset_type: "REAL",
    graph_mode: "REAL",
    finding_kind: "POTENTIAL_PATTERN_OF_INTEREST",
    flagged: true,
    graph_score: 64,
    evidence_confidence: 64,
    explanation:
      "Project has highly similar works in the same constituency sharing IDA and close recommendation dates.",
    project_node: projectNode(232, "Construction of roads in Hindupur", "internal:232"),
    connected_nodes: [...entities, ...similarNodes, ...peerNodes],
    relationships,
    graph_findings: [finding],
    graph_evidence: finding,
    stats: {
      connected_project_count: similarCount + peerCount,
      similar_project_count: similarCount,
      same_constituency_similar: similarCount,
      same_ida_similar: similarCount,
      close_dates_similar: similarCount,
    },
    mp_name: "Test MP",
    category: "Roads",
    constituency: "HINDUPUR",
    ida: "Hindupur_IDA",
    state: "Andhra Pradesh",
    candidate_strategy: "constituency+category+ida cluster; overlap blocking",
    gps_used: false,
    ...overrides,
  };
}

export function isolatedGraph(): GraphIntelligenceResponse {
  return sampleGraph(
    {
      finding_kind: "INSUFFICIENT_EVIDENCE",
      flagged: false,
      graph_score: null,
      evidence_confidence: 16,
      explanation: "No usable entity fields and no similar works were available.",
      connected_nodes: [],
      relationships: [],
      graph_findings: [
        {
          kind: "INSUFFICIENT_EVIDENCE",
          summary: "Insufficient evidence to describe connectivity.",
          details: "Entity fields and similar works were unavailable.",
          score: null,
          confidence: 16,
        },
      ],
      graph_evidence: {
        kind: "INSUFFICIENT_EVIDENCE",
        summary: "Insufficient evidence to describe connectivity.",
        details: "Entity fields and similar works were unavailable.",
        score: null,
        confidence: 16,
      },
      stats: { connected_project_count: 0, similar_project_count: 0 },
      mp_name: "",
      category: "",
      constituency: "",
      ida: "",
      state: "",
    },
    { similarCount: 0, peerCount: 0 },
  );
}
