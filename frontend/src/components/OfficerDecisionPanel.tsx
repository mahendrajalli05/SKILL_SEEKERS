"use client";

import { useState } from "react";

import type { OfficerDecision, OfficerDecisionType } from "@/lib/types";
import { officerActionLabel } from "@/lib/display";

const ACTIONS: OfficerDecisionType[] = [
  "confirm_concern",
  "dismiss",
  "need_more_info",
];

export function OfficerDecisionPanel({
  decisions,
  submitting,
  error,
  onSubmit,
}: {
  decisions: OfficerDecision[];
  submitting?: boolean;
  error?: string | null;
  onSubmit: (decisionType: OfficerDecisionType, reason: string) => Promise<void> | void;
}) {
  const [reason, setReason] = useState("");
  return (
    <section id="officer-decision" className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">Officer decision</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Human decision only. These actions are stored on the audit trail and do
        not change Investigation Priority or Evidence Confidence. This prototype
        does not record a legal fraud finding.
      </p>
      <label className="mt-4 block text-sm">
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
            onClick={() => onSubmit(action, reason)}
          >
            {officerActionLabel(action)}
          </button>
        ))}
      </div>
      {error ? <p className="mt-3 text-sm text-[var(--saffron)]">{error}</p> : null}
      <h3 className="mt-5 text-sm font-semibold text-[var(--navy)]">Recorded decisions</h3>
      {decisions.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--muted)]">No officer decision recorded yet.</p>
      ) : (
        <ul className="mt-2 space-y-2 text-sm">
          {decisions.map((item) => (
            <li key={item.id} className="border border-[var(--line)] p-3">
              <p className="font-medium">{officerActionLabel(item.decision_type)}</p>
              <p className="text-[var(--muted)]">{item.reason || "No reason recorded."}</p>
              <p className="text-xs text-[var(--muted)]">
                {item.created_at} · scores unchanged: {item.scores_unchanged ? "yes" : "no"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
