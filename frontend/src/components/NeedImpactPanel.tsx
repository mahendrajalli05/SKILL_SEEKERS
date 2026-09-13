"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { ScoreBar } from "@/components/system/ScoreDisplay";
import { fetchNeedImpact } from "@/lib/api";
import { formatAllocation } from "@/lib/display";
import type { DataMode, NeedImpactResponse } from "@/lib/types";

function scoreLabel(value: number | null | undefined, available: boolean, fallback = "INCONCLUSIVE") {
  if (!available || value == null) {
    return fallback;
  }
  return String(value);
}

export function NeedImpactPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [data, setData] = useState<NeedImpactResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const body = await fetchNeedImpact(projectId, mode);
      setData(body);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Need & Impact could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Need & Impact</h2>
        <p className="mt-2 text-sm text-[var(--saffron)]">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Need & Impact</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Loading need and impact assessment…</p>
      </section>
    );
  }

  return (
    <section id="need-impact" className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">Need & Impact</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">{data.governance_note}</p>
        <p className="mt-1 text-xs text-[var(--muted)]">{data.weight_note}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article className="svk-card p-4" data-tone="signal">
          <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-[var(--muted)]">NEED</p>
          <p className="svk-mono mt-2 text-2xl font-semibold">{scoreLabel(data.need_score, data.need.available)}</p>
          <ScoreBar value={data.need.available ? data.need_score : null} />
        </article>
        <article className="svk-card p-4" data-tone="indigo">
          <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-[var(--muted)]">IMPACT</p>
          <p className="svk-mono mt-2 text-2xl font-semibold">{scoreLabel(data.impact_score, data.impact.available)}</p>
          <ScoreBar value={data.impact.available ? data.impact_score : null} />
        </article>
        <article className="svk-card p-4" data-tone="saffron">
          <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-[var(--muted)]">URGENCY</p>
          <p className="svk-mono mt-2 text-2xl font-semibold">{scoreLabel(data.urgency_score, data.urgency.available)}</p>
          <ScoreBar value={data.urgency.available ? data.urgency_score : null} tone="priority" />
        </article>
        <article className="svk-card p-4" data-tone="success">
          <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-[var(--muted)]">PRIORITY</p>
          <p className="svk-mono mt-2 text-2xl font-semibold">
            {scoreLabel(data.priority_score, data.priority_class !== "INCONCLUSIVE")}
          </p>
          <p className="mt-1 text-xs">{data.priority_class}</p>
          <ScoreBar value={data.priority_class !== "INCONCLUSIVE" ? data.priority_score : null} />
        </article>
      </div>
      <dl>
        <FieldRow label="Project" value={data.work_description} />
        <FieldRow label="Constituency" value={data.constituency} />
        <FieldRow label="Category" value={data.category} />
        <FieldRow label="Requested amount" value={formatAllocation(data.requested_amount)} />
        <FieldRow
          label="Need Score"
          value={scoreLabel(data.need_score, data.need.available)}
        />
        <FieldRow
          label="Impact Score"
          value={scoreLabel(data.impact_score, data.impact.available)}
        />
        <FieldRow
          label="Priority Score"
          value={scoreLabel(data.priority_score, data.priority_class !== "INCONCLUSIVE")}
        />
        <FieldRow label="Recommended priority class" value={data.priority_class} />
        <FieldRow label="Evidence Confidence" value={data.evidence_confidence} />
        <FieldRow label="Data mode" value={data.data_mode} />
      </dl>
      {data.enrichment_label ? (
        <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
          {data.enrichment_label} enrichment is not a government fact
        </p>
      ) : null}
      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Top reasons</h3>
        {data.top_reasons.length === 0 ? (
          <p className="mt-1 text-sm text-[var(--muted)]">No scored reasons are available.</p>
        ) : (
          <ul className="mt-1 list-disc pl-5 text-sm">
            {data.top_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <h3 className="text-sm font-semibold text-[var(--navy)]">Unavailable inputs</h3>
        {data.unavailable_inputs.length === 0 ? (
          <p className="mt-1 text-sm text-[var(--muted)]">No unavailable scored inputs were listed.</p>
        ) : (
          <ul className="mt-1 list-disc pl-5 text-sm text-[var(--muted)]">
            {data.unavailable_inputs.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-sm">{data.explanation}</p>
      <p className="text-xs text-[var(--muted)]">
        This is not a funding approval. Automatic sanctioning is {String(data.automatic_sanction)}.
      </p>
    </section>
  );
}
