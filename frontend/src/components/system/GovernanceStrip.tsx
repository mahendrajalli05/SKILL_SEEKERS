import { GOVERNANCE_LINE, PRIORITY_NOT_LEGAL } from "@/lib/explanations";

export function GovernanceStrip({ compact = false }: { compact?: boolean }) {
  return (
    <p className="text-xs text-[var(--muted)]">
      {GOVERNANCE_LINE}
      {compact ? null : ` ${PRIORITY_NOT_LEGAL}`}
    </p>
  );
}

export function SourceBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center border border-[var(--line)] px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[var(--muted)]">
      {label}
    </span>
  );
}
