import Link from "next/link";

import type { CostComparable, OverlapMatch } from "@/lib/types";
import { displayText, formatAllocation, formatDate } from "@/lib/display";

export function ComparableProjects({
  cost,
  overlap,
  costNote,
}: {
  cost: CostComparable[];
  overlap: OverlapMatch[];
  costNote?: string;
}) {
  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">Comparable projects</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Comparables are returned by Cost Intelligence and Overlap Intelligence.
        Peers are not invented.
      </p>
      {costNote ? <p className="mt-2 text-xs text-[var(--muted)]">{costNote}</p> : null}

      <h3 className="mt-4 text-sm font-semibold text-[var(--navy)]">Cost peers</h3>
      {cost.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--muted)]">No cost comparables returned.</p>
      ) : (
        <ul className="mt-2 divide-y divide-[var(--line)]">
          {cost.map((item) => (
            <li key={`cost-${item.project_id}`} className="py-2 text-sm">
              <Link className="font-medium text-[var(--navy)]" href={`/projects/${item.project_id}`}>
                {item.internal_project_id}
              </Link>
              <p className="text-[var(--muted)]">
                {displayText(item.constituency)} · {displayText(item.category)} ·{" "}
                {formatAllocation(item.allocation_amount)} · {formatDate(item.recommended_date)}
              </p>
            </li>
          ))}
        </ul>
      )}

      <h3 className="mt-4 text-sm font-semibold text-[var(--navy)]">Overlap matches</h3>
      {overlap.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--muted)]">No overlap matches returned.</p>
      ) : (
        <ul className="mt-2 divide-y divide-[var(--line)]">
          {overlap.map((item) => (
            <li key={`overlap-${item.linked_project_id}`} className="py-2 text-sm">
              <Link
                className="font-medium text-[var(--navy)]"
                href={`/projects/${item.linked_project_id}`}
              >
                {item.linked_internal_project_id}
              </Link>
              <p>{displayText(item.linked_work_description)}</p>
              <p className="text-[var(--muted)]">
                {displayText(item.linked_constituency)} · {displayText(item.linked_category)} ·{" "}
                {item.outcome} · score {item.overall_overlap_score}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
