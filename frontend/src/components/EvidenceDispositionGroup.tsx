import { EvidenceCard } from "@/components/EvidenceCard";
import type { EvidenceObject } from "@/lib/types";

const GROUPS: { key: string; title: string; match: (item: EvidenceObject) => boolean }[] = [
  {
    key: "flagged",
    title: "WHY FLAGGED",
    match: (item) => item.disposition === "WHY_FLAGGED",
  },
  {
    key: "not-flagged",
    title: "WHY NOT FLAGGED",
    match: (item) => item.disposition === "WHY_NOT_FLAGGED",
  },
  {
    key: "inconclusive",
    title: "INCONCLUSIVE",
    match: (item) => item.disposition === "INCONCLUSIVE",
  },
  {
    key: "insufficient",
    title: "INSUFFICIENT EVIDENCE",
    match: (item) =>
      item.disposition === "NOT_ASSESSABLE" || item.status === "not_assessable",
  },
];

export function EvidenceDispositionGroup({ items }: { items: EvidenceObject[] }) {
  return (
    <div className="space-y-5">
      {GROUPS.map((group) => {
        const matched = items.filter(group.match);
        return (
          <section key={group.key}>
            <h3 className="font-semibold text-[var(--navy)]">{group.title}</h3>
            {matched.length === 0 ? (
              <p className="mt-2 text-sm text-[var(--muted)]">No {group.title.toLowerCase()} evidence in this view.</p>
            ) : (
              <div className="mt-2 space-y-3">
                {matched.map((item) => (
                  <EvidenceCard key={item.evidence_id} evidence={item} />
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
