"use client";

import Link from "next/link";
import { useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { formatAllocation } from "@/lib/display";
import type { DataMode, ProjectLifecycleResponse } from "@/lib/types";

const LIFECYCLE_PATHS = ["FUTURE", "ONGOING", "COMPLETED"] as const;

function statusClass(status: string) {
  const value = status.toUpperCase();
  if (value === "CURRENT") return "border-[var(--navy-fill)] bg-[var(--navy-fill)] text-white";
  if (value === "COMPLETED") return "border-[var(--signal)] text-[var(--navy)]";
  if (value === "INCONCLUSIVE") return "border-[var(--saffron)] text-[var(--saffron)]";
  return "border-[var(--line)] text-[var(--muted)]";
}

function textValue(value: unknown) {
  if (value == null || value === "") return "NOT AVAILABLE";
  return String(value);
}

export function ProjectLifecyclePanel({
  projectId,
  mode,
  lifecycle,
  loading,
  error,
  submitting,
  onPlanningDecision,
}: {
  projectId: number;
  mode: DataMode;
  lifecycle: ProjectLifecycleResponse | null;
  loading?: boolean;
  error?: string | null;
  submitting?: boolean;
  onPlanningDecision?: (action: string, reason: string) => Promise<void> | void;
}) {
  const [reason, setReason] = useState("");
  const modeQuery = mode === "REAL" ? "real" : "hybrid";
  const investigateHref = `/projects/${projectId}/investigate?mode=${modeQuery}`;
  const passportHref = `/projects/${projectId}?mode=${modeQuery}`;

  if (loading) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">LIFECYCLE</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Loading project lifecycle…</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">LIFECYCLE</h2>
        <p className="mt-2 text-sm text-[var(--saffron)]">{error}</p>
      </section>
    );
  }
  if (!lifecycle) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">LIFECYCLE</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Unavailable</p>
      </section>
    );
  }

  const current = lifecycle.lifecycle_state;
  const need = lifecycle.need_impact_summary;
  const risk = lifecycle.risk_summary;
  const summary = lifecycle.project_status_summary;

  const resolveHref = (href: string | null | undefined) => {
    if (!href) return investigateHref;
    if (href.startsWith("#")) return `${investigateHref}${href}`;
    if (href.startsWith("/investigate")) return investigateHref;
    return `${passportHref}${href.startsWith("#") ? href : ""}`;
  };

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">LIFECYCLE</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Places the work in Future, Ongoing, or Completed workflow using observed status.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">{lifecycle.governance_note}</p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Data mode: {lifecycle.data_mode}. This is not a sanction and not a legal fraud finding.
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        {LIFECYCLE_PATHS.map((path) => {
          const active = current === path;
          return (
            <div
              key={path}
              className={`border p-3 text-center text-sm font-medium ${
                active ? "border-[var(--navy-fill)] bg-[var(--navy-fill)] text-white" : "border-[var(--line)] text-[var(--muted)]"
              }`}
            >
              {path === "FUTURE" ? "Future" : path === "ONGOING" ? "Ongoing" : "Completed"}
              {active ? " (current)" : ""}
            </div>
          );
        })}
      </div>
      {current === "UNKNOWN" ? (
        <p className="text-sm text-[var(--saffron)]">
          SARVSAKSHI workflow state is UNKNOWN because source STATUS did not map to Future, Ongoing, or Completed.
        </p>
      ) : null}

      <dl>
        <FieldRow label="SARVSAKSHI workflow state" value={lifecycle.lifecycle_state} />
        <FieldRow label="Source status" value={lifecycle.source_status} />
        <FieldRow label="Current stage" value={lifecycle.current_stage} />
        {lifecycle.planning_state ? (
          <FieldRow label="Planning state" value={lifecycle.planning_state} />
        ) : null}
        <FieldRow label="Data mode" value={String(lifecycle.data_mode)} />
      </dl>

      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Workflow timeline</h3>
        <ol className="mt-2 space-y-2 text-sm">
          {lifecycle.timeline.map((node) => (
            <li key={node.stage} className={`border px-3 py-2 ${statusClass(node.status)}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>
                  {node.label} — {node.status}
                </span>
                {node.available ? (
                  <Link className="underline" href={resolveHref(node.href)}>
                    Open
                  </Link>
                ) : null}
              </div>
              {node.note ? <p className="mt-1 text-xs opacity-80">{node.note}</p> : null}
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Project status summary</h3>
        <dl className="mt-2">
          {Object.entries(summary).map(([key, value]) =>
            value == null || value === "" ? null : (
              <FieldRow key={key} label={key.replaceAll("_", " ")} value={textValue(value)} />
            ),
          )}
        </dl>
      </div>

      {current === "FUTURE" && need ? (
        <div>
          <h3 className="text-sm font-semibold text-[var(--navy)]">Future / Need & Impact</h3>
          <dl className="mt-2">
            <FieldRow label="Project" value={lifecycle.work_description} />
            <FieldRow label="Constituency" value={lifecycle.constituency} />
            <FieldRow label="Category" value={lifecycle.category} />
            <FieldRow label="Requested amount" value={formatAllocation(lifecycle.requested_amount)} />
            <FieldRow label="Need Score" value={textValue(need.need_score)} />
            <FieldRow label="Impact Score" value={textValue(need.impact_score)} />
            <FieldRow label="Priority" value={textValue(need.priority_class)} />
            <FieldRow label="Evidence Confidence" value={textValue(need.evidence_confidence)} />
          </dl>
          {Array.isArray(need.unavailable_inputs) && need.unavailable_inputs.length > 0 ? (
            <p className="mt-2 text-sm text-[var(--muted)]">
              Unavailable inputs: {(need.unavailable_inputs as string[]).join("; ")}
            </p>
          ) : null}
          <p className="mt-2 text-sm">{lifecycle.recommendation_rationale}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Priority recommendation only. The system does not sanction automatically.
          </p>
        </div>
      ) : null}

      {risk && risk.appropriate ? (
        <div>
          <h3 className="text-sm font-semibold text-[var(--navy)]">Risk Fusion V2</h3>
          <dl className="mt-2">
            <FieldRow label="Investigation Priority" value={textValue(risk.investigation_priority)} />
            <FieldRow label="Evidence Confidence" value={textValue(risk.evidence_confidence)} />
            <FieldRow label="Recommendation" value={textValue(risk.recommended_action)} />
          </dl>
          <Link className="mt-2 inline-block text-sm underline" href={`${investigateHref}#risk-fusion-v2`}>
            Open investigation workspace
          </Link>
        </div>
      ) : (
        <p className="text-sm text-[var(--muted)]">
          {typeof risk?.reason === "string"
            ? risk.reason
            : "Risk Fusion V2 is used for ongoing and completed investigation."}
        </p>
      )}

      {lifecycle.final_case_summary ? (
        <div>
          <h3 className="text-sm font-semibold text-[var(--navy)]">Final case summary</h3>
          <p className="mt-2 text-sm">{textValue(lifecycle.final_case_summary.result)}</p>
          <p className="mt-1 text-sm text-[var(--muted)]">{textValue(lifecycle.final_case_summary.note)}</p>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 text-sm">
        <Link className="underline" href={passportHref}>
          Digital Passport
        </Link>
        <Link className="underline" href={investigateHref}>
          Investigation Workspace
        </Link>
        {current === "FUTURE" ? (
          <Link className="underline" href={`${passportHref}#need-impact`}>
            Need & Impact
          </Link>
        ) : null}
        {current === "ONGOING" ? (
          <Link className="underline" href={`${investigateHref}#milestones`}>
            Milestones
          </Link>
        ) : null}
      </div>

      {current === "FUTURE" && onPlanningDecision ? (
        <div>
          <h3 className="text-sm font-semibold text-[var(--navy)]">Officer planning decision</h3>
          <p className="mt-1 text-xs text-[var(--muted)]">
            SARVSAKSHI workflow states only: PLANNING, PRIORITIZED, DEFERRED, NEEDS MORE INFORMATION.
            These actions do not sanction a project or release funds.
          </p>
          <textarea
            className="mt-2 w-full border border-[var(--line)] p-2 text-sm"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Reason (required for audit)"
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {["PRIORITIZE", "DEFER", "NEED_MORE_INFORMATION"].map((action) => (
              <button
                key={action}
                type="button"
                disabled={submitting}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => onPlanningDecision(action, reason)}
              >
                {action.replaceAll("_", " ")}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Workflow checkpoints</h3>
        <p className="mt-1 text-xs text-[var(--muted)]">
          PROCEED / HOLD / INSPECT are recorded on Milestone Advisor. CONFIRM CONCERN / DISMISS /
          NEED MORE INFORMATION are recorded on the Investigation Workspace. None of these are
          automatic sanctions or payments.
        </p>
        <p className="mt-2 text-sm">{lifecycle.checkpoint_actions.join(" · ")}</p>
      </div>
    </section>
  );
}
