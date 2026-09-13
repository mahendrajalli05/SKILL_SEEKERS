import type { SyntheticEnrichment } from "@/lib/types";
import { UNAVAILABLE_REAL_LABEL } from "@/lib/display";
import { FieldRow } from "@/components/FieldRow";

function syntheticValue(value: string | number | null | undefined): string {
  if (value == null || value === "") {
    return UNAVAILABLE_REAL_LABEL;
  }
  return String(value);
}

export function SyntheticFieldsPanel({
  enrichment,
  mode,
}: {
  enrichment: SyntheticEnrichment | null | undefined;
  mode: string;
}) {
  if (mode !== "HYBRID") {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">SYNTHETIC prototype enrichment</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          REAL DATA mode does not use synthetic enrichment. Missing government
          fields remain {UNAVAILABLE_REAL_LABEL.toLowerCase()}.
        </p>
      </section>
    );
  }
  if (!enrichment) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">SYNTHETIC prototype enrichment</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          No HYBRID enrichment row is linked to this work. Observed real fields
          only.
        </p>
      </section>
    );
  }
  return (
    <section className="border border-[var(--saffron)] bg-[#f8efe6] p-5">
      <h2 className="font-semibold text-[var(--navy)]">SYNTHETIC prototype enrichment</h2>
      <p className="mt-1 text-sm">{enrichment.disclaimer}</p>
      <dl className="mt-3">
        <FieldRow label="Implementing district" value={syntheticValue(enrichment.implementing_district)} synthetic />
        <FieldRow label="Vendor" value={syntheticValue(enrichment.vendor_name)} synthetic />
        <FieldRow label="Sanction date" value={syntheticValue(enrichment.sanction_date)} synthetic />
        <FieldRow label="Start date" value={syntheticValue(enrichment.start_date)} synthetic />
        <FieldRow label="Completion date" value={syntheticValue(enrichment.completion_date)} synthetic />
        <FieldRow
          label="Expenditure"
          value={enrichment.expenditure == null ? UNAVAILABLE_REAL_LABEL : String(enrichment.expenditure)}
          synthetic
        />
        <FieldRow
          label="GPS"
          value={
            enrichment.gps_latitude == null || enrichment.gps_longitude == null
              ? UNAVAILABLE_REAL_LABEL
              : `${enrichment.gps_latitude}, ${enrichment.gps_longitude}`
          }
          synthetic
        />
        <FieldRow
          label="Physical progress"
          value={
            enrichment.physical_progress_percent == null
              ? UNAVAILABLE_REAL_LABEL
              : `${enrichment.physical_progress_percent}%`
          }
          synthetic
        />
        <FieldRow
          label="Milestones"
          value={
            enrichment.milestones?.number == null
              ? UNAVAILABLE_REAL_LABEL
              : `${enrichment.milestones.number} / total ${enrichment.milestones.total_amount ?? UNAVAILABLE_REAL_LABEL}`
          }
          synthetic
        />
      </dl>
    </section>
  );
}
