import { StatusBadge } from "@/components/ui/StatusBadge";
import type { EvidenceObject } from "@/lib/types";

export function EvidenceTimeline({ items }: { items: EvidenceObject[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-[var(--muted)]">No supporting evidence has been recorded yet.</p>
    );
  }
  return (
    <ol className="relative space-y-3 border-l border-[var(--line)] pl-4">
      {items.map((item, index) => (
        <li
          key={item.evidence_id}
          className="svk-reveal relative"
          style={{ animationDelay: `${index * 60}ms` }}
        >
          <span className="absolute -left-[1.15rem] top-1.5 h-2 w-2 rounded-full bg-[var(--signal)]" />
          <p className="svk-mono text-xs text-[var(--muted)]">
            {item.created_at ?? "Timestamp unavailable"}
          </p>
          <p className="mt-0.5 text-sm text-[var(--navy)]">
            {item.engine_name} · {item.finding}
          </p>
          <div className="mt-1 flex flex-wrap gap-2">
            <StatusBadge value={String(item.data_mode)} />
            <StatusBadge value={item.disposition} />
          </div>
        </li>
      ))}
    </ol>
  );
}
