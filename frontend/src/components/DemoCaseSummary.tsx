import { FieldRow } from "@/components/FieldRow";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { officerActionLabel, recommendedActionLabel } from "@/lib/display";
import type { DemoCaseSummary } from "@/lib/types";

export function DemoCaseSummary({ summary }: { summary: DemoCaseSummary }) {
  const signals = summary.main_signals
    .map((item) => String(item.group ?? item.status ?? ""))
    .filter(Boolean);
  return (
    <section id="summary" className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">FINAL CASE SUMMARY</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">{summary.demo_notice}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusBadge kind="DEMO" />
        <StatusBadge value={summary.data_reliability} />
        <StatusBadge value={summary.data_mode} />
      </div>
      <dl className="mt-4">
        <FieldRow label="Project" value={summary.project.work_description} />
        <FieldRow label="Scheme ID" value={summary.project.scheme_id} />
        <FieldRow label="Internal Project ID" value={summary.project.internal_project_id} />
        <FieldRow label="Lifecycle" value={summary.lifecycle} />
        <FieldRow
          label="Investigation Priority"
          value={summary.investigation_priority == null ? null : `${summary.investigation_priority}/100`}
        />
        <FieldRow
          label="Evidence Confidence"
          value={summary.evidence_confidence == null ? null : `${summary.evidence_confidence}/100`}
        />
        <FieldRow label="Main signals" value={signals.length ? signals.join(", ") : "None recorded"} />
        <FieldRow
          label="Evidence"
          value={summary.evidence.length ? summary.evidence.join(", ") : "None recorded"}
        />
        <FieldRow
          label="Missing information"
          value={summary.missing_information.length ? summary.missing_information.join("; ") : "None listed"}
        />
        <FieldRow
          label="Recommended action"
          value={recommendedActionLabel(summary.recommended_action)}
        />
        <FieldRow
          label="Officer decision"
          value={summary.officer_decision ? officerActionLabel(summary.officer_decision) : "Not recorded"}
        />
        <FieldRow label="REAL / HYBRID / SYNTHETIC" value={summary.data_reliability} />
      </dl>
      <p className="mt-4 text-sm text-[var(--muted)]">
        Automatic sanction: no. Payment release: no. Legal fraud conclusion: no.
        Officer decisions do not change Investigation Priority.
      </p>
    </section>
  );
}
