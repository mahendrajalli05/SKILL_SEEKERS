"use client";

import { useMemo, useRef, useState } from "react";

import type { GraphRelationship } from "@/lib/types";
import {
  GRAPH_VIEWBOX_HEIGHT,
  GRAPH_VIEWBOX_WIDTH,
  type PlacedNode,
  type VisibleNeighborhood,
  nodeById,
  truncateLabel,
} from "@/lib/graphView";

const NODE_FILL: Record<string, string> = {
  PROJECT: "#4ea3ff",
  MP: "#7eb6ff",
  CONSTITUENCY: "#5b8fb8",
  CATEGORY: "#8fb4d9",
  IDA: "#d4a45a",
  STATE: "#9aa8b8",
};

function nodeFill(type: string, ring: PlacedNode["ring"]): string {
  if (ring === "similar") {
    return "#4ea3ff";
  }
  if (ring === "peer") {
    return "#6d7f93";
  }
  return NODE_FILL[type] ?? "#5c6570";
}

function nodeRadius(ring: PlacedNode["ring"]): number {
  if (ring === "center") {
    return 28;
  }
  if (ring === "entity") {
    return 20;
  }
  return 16;
}

function edgeKey(rel: GraphRelationship, index: number): string {
  return `${rel.from_node_id}|${rel.edge_type}|${rel.to_node_id}|${index}`;
}

export function RelationshipGraphView({
  neighborhood,
  selectedNodeId,
  selectedEdgeKey,
  onSelectNode,
  onSelectEdge,
}: {
  neighborhood: VisibleNeighborhood;
  selectedNodeId: string | null;
  selectedEdgeKey: string | null;
  onSelectNode: (nodeId: string) => void;
  onSelectEdge: (rel: GraphRelationship, key: string) => void;
}) {
  const [hover, setHover] = useState<{
    label: string;
    x: number;
    y: number;
  } | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, k: 1 });
  const drag = useRef<{ x: number; y: number; vx: number; vy: number } | null>(null);

  const placedById = useMemo(() => {
    const map = new Map<string, PlacedNode>();
    for (const item of neighborhood.nodes) {
      map.set(item.node.node_id, item);
    }
    return map;
  }, [neighborhood.nodes]);

  const resetView = () => setView({ x: 0, y: 0, k: 1 });

  return (
    <div className="relative border border-[var(--line)] bg-[var(--surface-2)]">
      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--line)] p-2 text-xs">
        <button type="button" className="svk-btn" onClick={resetView}>
          Reset
        </button>
        <span className="self-center text-[var(--muted)]">Scroll to zoom. Drag to pan. Keyboard: Enter selects a node.</span>
        <span className="flex flex-wrap gap-2">
          <LegendDot color="#4ea3ff" label="Central project" />
          <LegendDot color="#7eb6ff" label="Connected entity" />
          <LegendDot color="#6d7f93" label="Connected project" />
        </span>
      </div>
      <svg
        role="img"
        aria-label="Project relationship neighborhood graph"
        viewBox={`0 0 ${GRAPH_VIEWBOX_WIDTH} ${GRAPH_VIEWBOX_HEIGHT}`}
        className="h-[min(70vh,32rem)] w-full cursor-grab focus-visible:outline"
        onWheel={(event) => {
          event.preventDefault();
          const factor = event.deltaY < 0 ? 1.12 : 0.9;
          setView((current) => ({
            ...current,
            k: Math.min(3, Math.max(0.4, current.k * factor)),
          }));
        }}
        onPointerDown={(event) => {
          drag.current = {
            x: event.clientX,
            y: event.clientY,
            vx: view.x,
            vy: view.y,
          };
        }}
        onPointerMove={(event) => {
          if (!drag.current) {
            return;
          }
          const dx = event.clientX - drag.current.x;
          const dy = event.clientY - drag.current.y;
          setView((current) => ({
            ...current,
            x: drag.current ? drag.current.vx + dx : current.x,
            y: drag.current ? drag.current.vy + dy : current.y,
          }));
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
        onPointerLeave={() => {
          drag.current = null;
          setHover(null);
        }}
      >
        <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
          {neighborhood.edges.map((rel, index) => {
            const from = placedById.get(rel.from_node_id);
            const to = placedById.get(rel.to_node_id);
            if (!from || !to) {
              return null;
            }
            const key = edgeKey(rel, index);
            const active = selectedEdgeKey === key;
            const relatedToSelection =
              selectedNodeId != null &&
              (rel.from_node_id === selectedNodeId || rel.to_node_id === selectedNodeId);
            return (
              <g key={key}>
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={active || relatedToSelection ? "#d4a45a" : "rgba(154,176,201,0.35)"}
                  strokeWidth={rel.edge_type === "SIMILAR_TO" ? 2.4 : 1.6}
                  strokeDasharray={rel.edge_type === "SIMILAR_TO" ? "6 4" : undefined}
                />
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="transparent"
                  strokeWidth={12}
                  role="button"
                  tabIndex={0}
                  aria-label={`${rel.edge_type} ${rel.from_node_id} ${rel.to_node_id}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectEdge(rel, key);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      onSelectEdge(rel, key);
                    }
                  }}
                  onMouseEnter={(event) => {
                    const svg = event.currentTarget.ownerSVGElement;
                    const rect = svg?.getBoundingClientRect();
                    setHover({
                      label: `${rel.edge_type} · strength ${rel.strength.toFixed(2)}`,
                      x: event.clientX - (rect?.left ?? 0),
                      y: event.clientY - (rect?.top ?? 0),
                    });
                  }}
                  onMouseLeave={() => setHover(null)}
                />
              </g>
            );
          })}
          {neighborhood.nodes.map((item) => {
            const selected = selectedNodeId === item.node.node_id;
            const radius = nodeRadius(item.ring);
            return (
              <g
                key={item.node.node_id}
                transform={`translate(${item.x} ${item.y})`}
                role="button"
                tabIndex={0}
                aria-label={`${item.node.node_type} ${item.node.label}`}
                data-node-type={item.node.node_type}
                data-ring={item.ring}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelectNode(item.node.node_id);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    onSelectNode(item.node.node_id);
                  }
                }}
                onMouseEnter={(event) => {
                  const svg = event.currentTarget.ownerSVGElement;
                  const rect = svg?.getBoundingClientRect();
                  const relHint =
                    item.ring === "similar"
                      ? "SIMILAR_TO project"
                      : item.ring === "entity"
                        ? `${item.node.node_type} entity`
                        : item.ring === "center"
                          ? "Central project"
                          : "Connected project";
                  setHover({
                    label: `${item.node.node_type}: ${item.node.label} · ${relHint}`,
                    x: event.clientX - (rect?.left ?? 0),
                    y: event.clientY - (rect?.top ?? 0),
                  });
                }}
                onMouseLeave={() => setHover(null)}
              >
                <circle
                  r={radius}
                  fill={item.ring === "center" ? "#4ea3ff" : "#101820"}
                  stroke={selected ? "#d4a45a" : nodeFill(item.node.node_type, item.ring)}
                  strokeWidth={selected ? 4 : 3}
                />
                <text
                  textAnchor="middle"
                  dy="0.35em"
                  fontSize={item.ring === "center" ? 9 : 8}
                  fill={item.ring === "center" ? "#071018" : "#d7e4f4"}
                >
                  {item.ring === "center" ? "PROJECT" : item.node.node_type}
                </text>
                <text
                  textAnchor="middle"
                  y={radius + 14}
                  fontSize={10}
                  fill="#d7e4f4"
                >
                  {truncateLabel(item.node.label, item.ring === "center" ? 28 : 18)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      {hover ? (
        <div
          className="pointer-events-none absolute max-w-xs border border-[var(--signal)] bg-[var(--surface)] px-2 py-1 text-xs"
          style={{ left: hover.x + 12, top: hover.y + 12 }}
        >
          {hover.label}
        </div>
      ) : null}
      {selectedNodeId ? (
        <p className="sr-only">
          Selected {nodeById(neighborhood.nodes, selectedNodeId)?.node.node_type}
        </p>
      ) : null}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-[var(--muted)]">
      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
