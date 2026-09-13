import type { ReactNode } from "react";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function normalizeHighlightQuery(query: string | null | undefined): string {
  return (query ?? "").trim();
}

export function HighlightedText({
  text,
  query,
}: {
  text: string | null | undefined;
  query: string | null | undefined;
}): ReactNode {
  const value = text ?? "";
  const needle = normalizeHighlightQuery(query);
  if (!value || !needle) {
    return value;
  }
  try {
    const matcher = new RegExp(escapeRegExp(needle), "ig");
    const parts = value.split(matcher);
    const hits = value.match(matcher);
    if (!hits || hits.length === 0) {
      return value;
    }
    const nodes: ReactNode[] = [];
    parts.forEach((part, index) => {
      nodes.push(part);
      if (index < hits.length) {
        nodes.push(
          <mark key={`h-${index}`} className="bg-yellow-100 text-[var(--navy)]">
            {hits[index]}
          </mark>,
        );
      }
    });
    return nodes;
  } catch {
    return value;
  }
}
