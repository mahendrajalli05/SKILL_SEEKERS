"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { fetchCitizenReports, fetchCitizenSummary } from "@/lib/api";
import type { CitizenReport, CitizenSummary, DataMode } from "@/lib/types";

function statusClass(status: string) {
  if (status === "REJECTED" || status === "LOCATION_REJECTED") {
    return "border-[var(--saffron)] bg-[#f8efe6]";
  }
  if (status === "ACCEPTED" || status === "LOCATION_VERIFIED") {
    return "border-[var(--navy)] bg-white";
  }
  return "border-[var(--line)] bg-[#f6f7f9]";
}

export function JanSakshiPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [summary, setSummary] = useState<CitizenSummary | null>(null);
  const [reports, setReports] = useState<CitizenReport[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [summaryBody, list] = await Promise.all([
        fetchCitizenSummary(projectId, mode),
        fetchCitizenReports(projectId, mode),
      ]);
      setSummary(summaryBody);
      setReports(list.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jan-Sakshi could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">JAN-SAKSHI</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Citizen field evidence is supporting evidence only. One report does not establish
          truth. GPS is verification data and is not shown here.
        </p>
      </div>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      {summary ? (
        <dl>
          <FieldRow label="Verified reports" value={String(summary.verified_location_submissions)} />
          <FieldRow label="Rejected reports" value={String(summary.rejected_submissions)} />
          <FieldRow
            label="Satisfaction distribution"
            value={Object.entries(summary.satisfaction_distribution)
              .map(([score, count]) => `${score}: ${count}`)
              .join(" · ")}
          />
          <FieldRow
            label="Recurring issues"
            value={
              summary.recurring_issue_categories.length
                ? summary.recurring_issue_categories.map((item) => `${item.label} (${item.count})`).join(", ")
                : "none"
            }
          />
          <FieldRow label="Citizen evidence confidence" value={String(summary.citizen_evidence_confidence)} />
          <FieldRow label="Sample" value={summary.sample_size_status} />
        </dl>
      ) : (
        <p className="text-sm text-[var(--muted)]">Loading citizen summary…</p>
      )}
      <div className="space-y-3">
        {reports.map((report) => (
          <article key={report.citizen_report_id} className={`space-y-2 border p-4 ${statusClass(report.submission_status)}`}>
            <p className="text-sm font-medium">
              Report {report.citizen_report_id}: {report.submission_status} / {report.verification_result}
            </p>
            <p className="text-sm">Satisfaction: {report.satisfaction_rating ?? "unavailable"}</p>
            <p className="text-sm">Issue: {report.issue_category ?? "not specified"}</p>
            <p className="text-sm">{report.observation_text || "No observation text."}</p>
            <p className="text-xs text-[var(--muted)]">
              Location verification: {report.location_verification.result}. Distance and raw GPS are not shown.
            </p>
              {report.thumbnail_data_url ? (
                <img
                  src={report.thumbnail_data_url}
                  alt="Citizen evidence thumbnail"
                  className="h-20 w-20 object-cover"
                />
              ) : null}
            {report.duplicate?.flagged ? (
              <p className="text-xs text-[var(--saffron)]">{report.duplicate.flag}: review only, not a fraud finding.</p>
            ) : null}
            {report.plan_claim_evidence ? (
              <p className="text-xs">
                Plan → Claim → Evidence: {report.plan_claim_evidence.result}. Claim is not marked false.
              </p>
            ) : null}
            {report.synthetic_badge ? (
              <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">{report.synthetic_badge}</p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
