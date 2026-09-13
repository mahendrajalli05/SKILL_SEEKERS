import Link from "next/link";

import { FieldRow } from "@/components/FieldRow";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { DataMode, ProjectDetail } from "@/lib/types";
import { SCHEME_ID_NOTE, displayText, formatAllocation, formatDate } from "@/lib/display";

export function ProjectHeader({
  project,
  dataMode,
  investigateHref,
  passportHref,
}: {
  project: ProjectDetail;
  dataMode?: DataMode | string;
  investigateHref?: string;
  passportHref?: string;
}) {
  const mode = dataMode ?? project.data_mode ?? "HYBRID";
  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Project identity
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-[var(--navy)]">
            {displayText(project.work_description)}
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">{SCHEME_ID_NOTE}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge kind={String(mode) === "REAL" ? "REAL" : "HYBRID"} />
          <StatusBadge value={project.lifecycle_stage} />
          {passportHref ? (
            <Link
              href={passportHref}
              className="svk-btn"
            >
              Digital Passport
            </Link>
          ) : null}
          {investigateHref ? (
            <Link
              href={investigateHref}
              className="svk-btn svk-btn-primary"
            >
              Investigation workspace
            </Link>
          ) : null}
        </div>
      </div>
      <dl className="mt-4">
        <FieldRow label="SARVSAKSHI Scheme ID" value={project.scheme_id} hint={SCHEME_ID_NOTE} />
        <FieldRow label="Internal Project ID" value={project.internal_project_id} />
        <FieldRow label="Data Mode" value={String(mode)} />
        <FieldRow label="Constituency" value={project.constituency} />
        <FieldRow label="Category" value={project.category} />
        <FieldRow label="Status" value={project.status} />
        <FieldRow label="MP" value={project.mp_name} />
        <FieldRow label="State" value={project.state} />
        <FieldRow
          label="Allocation"
          value={formatAllocation(project.allocation_amount)}
          hint={project.amount_unit_note}
        />
        <FieldRow label="Recommendation date" value={formatDate(project.recommended_date)} />
      </dl>
    </section>
  );
}
