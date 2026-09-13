"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { assessMilestone, fetchProjectMilestones, submitMilestoneDecision } from "@/lib/api";
import { officerActionLabel } from "@/lib/display";
import type { DataMode, MilestoneOfficerAction, MilestoneRecord, ProjectMilestonesResponse } from "@/lib/types";

const ACTIONS: MilestoneOfficerAction[] = ["PROCEED", "HOLD", "INSPECT", "NEED_MORE_INFORMATION"];

function money(value: number | null | undefined, available: boolean | undefined, synthetic?: boolean) {
  if (!available || value == null) {
    return "unavailable";
  }
  return synthetic ? `${value} (SYNTHETIC)` : String(value);
}

export function MilestoneAdvisorPanel({
  projectId,
  mode,
  compact = false,
}: {
  projectId: number;
  mode: DataMode;
  compact?: boolean;
}) {
  const [data, setData] = useState<ProjectMilestonesResponse | null>(null);
  const [current, setCurrent] = useState<MilestoneRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await fetchProjectMilestones(projectId, mode);
      setData(body);
      const targetId = body.current_milestone_id ?? body.items[0]?.milestone_id;
      if (targetId) {
        const existing = body.items.find((item) => item.milestone_id === targetId) ?? body.current_milestone;
        if (existing?.recommendation) {
          setCurrent(existing);
        } else {
          const assessed = await assessMilestone(targetId, mode);
          setCurrent(assessed);
          const refreshed = await fetchProjectMilestones(projectId, mode);
          setData(refreshed);
        }
      } else {
        setCurrent(null);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Milestones could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onDecision = async (action: MilestoneOfficerAction) => {
    if (!current) {
      return;
    }
    setSubmitting(true);
    try {
      const updated = await submitMilestoneDecision(current.milestone_id, {
        action,
        reason,
        actor_role: "officer",
        data_mode: mode,
      });
      setCurrent(updated);
      const refreshed = await fetchProjectMilestones(projectId, mode);
      setData(refreshed);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Officer action could not be stored.");
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !data) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Milestones</h2>
        <p className="mt-2 text-sm text-[var(--saffron)]">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Milestones</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Loading milestone advisor…</p>
      </section>
    );
  }

  const shown = current ?? data.current_milestone;
  const hybrid = mode !== "REAL";

  return (
    <section id="milestones" className="space-y-4 svk-panel p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">Milestones</h2>
        <p className="mt-1 text-sm font-medium text-[var(--navy)]">MILESTONE & FUNDING REVIEW</p>
        <p className="mt-1 text-sm text-[var(--muted)]">{data.governance_note}</p>
        <p className="mt-1 text-sm text-[var(--muted)]">No automatic fund release or payment is performed.</p>
        {hybrid && data.hybrid_notice ? (
          <p className="mt-2 border border-[var(--saffron)] bg-[#f8efe6] p-2 text-sm">{data.hybrid_notice}</p>
        ) : null}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <article className="svk-card p-4" data-tone="indigo">
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">CURRENT STAGE</p>
          <p className="mt-1 font-semibold">{shown?.milestone_name ?? data.current_milestone_name ?? "Unavailable"}</p>
        </article>
        <article className="svk-card p-4" data-tone="signal">
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Evidence Readiness</p>
          <p className="mt-1 font-semibold">{shown?.evidence_status ?? "Unavailable"}</p>
        </article>
        <article className="svk-card p-4" data-tone="saffron">
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">AI RECOMMENDATION</p>
          <p className="mt-1 font-semibold">{shown?.recommendation ?? data.current_recommendation ?? "Unavailable"}</p>
        </article>
      </div>
      <dl>
        <FieldRow label="Project" value={data.work_description} />
        <FieldRow label="Current milestone" value={shown?.milestone_name ?? data.current_milestone_name} />
        <FieldRow
          label="Planned amount"
          value={money(shown?.planned_amount, shown?.amounts?.planned_amount_available ?? shown?.planned_amount != null)}
          synthetic={Boolean(shown?.synthetic && shown?.planned_amount != null)}
        />
        <FieldRow
          label="Claimed progress"
          value={
            shown?.progress?.claimed_progress_available
              ? `${shown.progress?.claimed_progress}%`
              : "unavailable"
          }
        />
        <FieldRow label="Evidence status" value={shown?.evidence_status} />
        <FieldRow label="Investigation Priority" value={data.investigation_priority} />
        <FieldRow label="Evidence Confidence" value={data.evidence_confidence} />
        <FieldRow label="Advisor Recommendation" value={shown?.recommendation ?? data.current_recommendation} />
        <FieldRow label="Data mode" value={data.data_mode} />
      </dl>
      {shown?.synthetic ? (
        <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
          SYNTHETIC milestone values are not official MPLADS records
        </p>
      ) : null}

      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Timeline</h3>
        <ol className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          {data.timeline.map((node, index) => (
            <li key={node.slot} className="flex items-center gap-2">
              <span className="border border-[var(--line)] px-2 py-1">
                <span className="font-medium">{node.slot}</span>
                {node.planned_date ? ` · ${node.planned_date}` : ""}
                {node.claim ? ` · ${node.claim}` : ""}
                {node.evidence ? ` · ${node.evidence}` : ""}
                {node.result ? ` · ${node.result}` : ""}
                {node.officer_action ? ` · ${officerActionLabel(node.officer_action)}` : ""}
              </span>
              {index < data.timeline.length - 1 ? <span aria-hidden="true">→</span> : null}
            </li>
          ))}
        </ol>
      </div>

      {compact ? (
        <p className="text-xs text-[var(--muted)]">{data.no_payment_note}</p>
      ) : (
        <>
          <div>
              <h3 className="text-sm font-semibold text-[var(--navy)]">WHY?</h3>
              <p className="text-xs uppercase tracking-wide text-[var(--muted)]">AI RECOMMENDATION</p>
            <p className="mt-1 text-sm">{shown?.assessment?.explanation ?? "Assessment has not been recorded yet."}</p>
            <h4 className="mt-3 text-xs uppercase tracking-wide text-[var(--muted)]">Supporting evidence</h4>
            <ul className="mt-1 list-disc pl-5 text-sm">
              {(shown?.assessment?.supporting_evidence ?? []).length === 0 ? (
                <li className="text-[var(--muted)]">None recorded.</li>
              ) : (
                shown?.assessment?.supporting_evidence.map((item) => <li key={item}>{item}</li>)
              )}
            </ul>
            <h4 className="mt-3 text-xs uppercase tracking-wide text-[var(--muted)]">Conflicting evidence</h4>
            <ul className="mt-1 list-disc pl-5 text-sm">
              {(shown?.assessment?.conflicting_evidence ?? []).length === 0 ? (
                <li className="text-[var(--muted)]">None recorded.</li>
              ) : (
                shown?.assessment?.conflicting_evidence.map((item) => <li key={item}>{item}</li>)
              )}
            </ul>
            <h4 className="mt-3 text-xs uppercase tracking-wide text-[var(--muted)]">Missing evidence</h4>
            <ul className="mt-1 list-disc pl-5 text-sm">
              {(shown?.assessment?.missing_evidence ?? []).length === 0 ? (
                <li className="text-[var(--muted)]">None recorded.</li>
              ) : (
                shown?.assessment?.missing_evidence.map((item) => <li key={item}>{item}</li>)
              )}
            </ul>
            <h4 className="mt-3 text-xs uppercase tracking-wide text-[var(--muted)]">Relevant intelligence signals</h4>
            <ul className="mt-1 list-disc pl-5 text-sm">
              {(shown?.assessment?.intelligence_signals ?? []).length === 0 ? (
                <li className="text-[var(--muted)]">No stored intelligence signal was attached.</li>
              ) : (
                shown?.assessment?.intelligence_signals.map((item) => <li key={item}>{item}</li>)
              )}
            </ul>
          </div>
          {shown ? (
            <div className="svk-card mt-4 space-y-3 p-4" data-tone="saffron">
              <h3 className="text-sm font-semibold text-[var(--navy)]">OFFICER DECISION</h3>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Recorded in the SARVSAKSHI workflow only. These buttons do not release money, approve
                PFMS payment, or change Investigation Priority.
              </p>
              <label className="mt-3 block text-sm">
                Reason
                <textarea
                  className="mt-1 w-full border border-[var(--line)] p-2"
                  rows={3}
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
              <div className="mt-3 flex flex-wrap gap-2">
                {ACTIONS.map((action) => (
                  <button
                    key={action}
                    type="button"
                    disabled={submitting}
                    className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                    onClick={() => void onDecision(action)}
                  >
                    {officerActionLabel(action)}
                  </button>
                ))}
              </div>
              {error ? <p className="mt-3 text-sm text-[var(--saffron)]">{error}</p> : null}
              {shown.officer_action ? (
                <p className="mt-3 text-sm">
                  Last officer action: {officerActionLabel(shown.officer_action)}. Scores unchanged.
                </p>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-[var(--muted)]">No milestone has been recorded for this work yet.</p>
          )}
          <p className="text-xs text-[var(--muted)]">{data.no_payment_note}</p>
        </>
      )}
    </section>
  );
}
