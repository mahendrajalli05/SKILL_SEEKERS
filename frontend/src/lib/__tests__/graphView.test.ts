import { describe, expect, it } from "vitest";

import {
  DEFAULT_VISIBLE_SIMILAR,
  GRAPH_FINDING_KINDS,
  GRAPH_PRIORITY_NOTE,
  buildVisibleNeighborhood,
  findingKindLabel,
  graphResultDataMode,
  relationshipDetailRows,
} from "@/lib/graphView";
import { isolatedGraph, sampleGraph } from "@/test/graphFixtures";

describe("graphView", () => {
  it("keeps the central project and API node types", () => {
    const visible = buildVisibleNeighborhood(sampleGraph());
    const types = visible.nodes.map((item) => item.node.node_type);
    expect(visible.nodes[0]?.ring).toBe("center");
    expect(visible.nodes[0]?.node.node_type).toBe("PROJECT");
    expect(types).toEqual(expect.arrayContaining(["PROJECT", "MP", "CONSTITUENCY", "CATEGORY", "IDA", "STATE"]));
    expect(visible.edges.map((rel) => rel.edge_type)).toEqual(
      expect.arrayContaining([
        "RECOMMENDED_BY",
        "LOCATED_IN_CONSTITUENCY",
        "HAS_CATEGORY",
        "ASSOCIATED_WITH_IDA",
        "IN_STATE",
        "SIMILAR_TO",
      ]),
    );
  });

  it("limits large similar neighborhoods and ranks by strength", () => {
    const graph = sampleGraph({}, { similarCount: 20, peerCount: 5 });
    const limited = buildVisibleNeighborhood(graph, DEFAULT_VISIBLE_SIMILAR, 0);
    const similar = limited.nodes.filter((item) => item.ring === "similar");
    expect(similar).toHaveLength(DEFAULT_VISIBLE_SIMILAR);
    expect(limited.hiddenSimilarCount).toBe(8);
    expect(limited.hiddenPeerCount).toBe(5);
    expect(limited.nodes.length).toBeLessThan(graph.connected_nodes!.length + 1);
    const first = similar[0]?.node.project_id;
    const last = similar[similar.length - 1]?.node.project_id;
    expect(first).toBe(3700);
    expect(last).toBe(3711);
  });

  it("does not invent relationships for isolated graphs", () => {
    const visible = buildVisibleNeighborhood(isolatedGraph());
    expect(visible.isolated).toBe(true);
    expect(visible.nodes).toHaveLength(1);
    expect(visible.edges).toHaveLength(0);
  });

  it("preserves finding kinds and REAL versus HYBRID", () => {
    expect(GRAPH_FINDING_KINDS).toContain("NORMAL_CONNECTIVITY");
    expect(findingKindLabel("POTENTIAL_PATTERN_OF_INTEREST")).toBe(
      "POTENTIAL_PATTERN_OF_INTEREST",
    );
    expect(graphResultDataMode(sampleGraph())).toBe("REAL");
    expect(graphResultDataMode(sampleGraph({ graph_mode: "HYBRID_TEST", dataset_type: "HYBRID" }))).toBe(
      "HYBRID",
    );
    expect(graphResultDataMode(sampleGraph(), true)).toBe("SYNTHETIC");
  });

  it("formats SIMILAR_TO details from API attributes", () => {
    const rel = sampleGraph().relationships!.find((item) => item.edge_type === "SIMILAR_TO")!;
    const rows = relationshipDetailRows(rel);
    expect(rows).toEqual(
      expect.arrayContaining([
        { label: "Edge type", value: "SIMILAR_TO" },
        { label: "Similarity", value: "0.91" },
        { label: "Same constituency", value: "YES" },
        { label: "Same category", value: "YES" },
        { label: "Recommendation gap", value: "18 days" },
      ]),
    );
    expect(GRAPH_PRIORITY_NOTE.toLowerCase()).toContain("does not modify investigation priority");
    expect(JSON.stringify(rows).toLowerCase()).not.toContain("fraud");
  });
});
