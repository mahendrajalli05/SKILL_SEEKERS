"use client";

import { useMemo, useState } from "react";

import { DataModeBanner } from "@/components/DataModeBanner";
import { PageHeader } from "@/components/system/PageHeader";
import { ProjectSelector } from "@/components/system/ProjectSelector";
import { BudgetMeter } from "@/components/system/VisualKit";
import { WorkflowStepper } from "@/components/system/WorkflowStepper";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { rankNeedImpact } from "@/lib/api";
import { DECISION_SUPPORT_ONLY, FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { displayText, formatAllocation } from "@/lib/display";
import type { DataMode, NeedImpactRankResponse, ProjectSearchItem } from "@/lib/types";

function parseIds(text: string): number[] {
  return Array.from(
    new Set(
      text
        .split(/[\s,;]+/)
        .map((item) => Number(item.trim()))
        .filter((item) => Number.isInteger(item) && item > 0),
    ),
  );
}

function budgetLabel(value: boolean | null) {
  if (value == null) {
    return "Not simulated";
  }
  return value ? "Inside hypothetical budget" : "Outside remaining hypothetical budget";
}

export default function NeedImpactPage() {
  const [mode, setMode] = useState<DataMode>("HYBRID");
  const [idsText, setIdsText] = useState("");
  const [selected, setSelected] = useState<ProjectSearchItem[]>([]);
  const [budgetCrore, setBudgetCrore] = useState("50");
  const [result, setResult] = useState<NeedImpactRankResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ids = useMemo(() => {
    const fromText = parseIds(idsText);
    const fromSelected = selected.map((item) => item.id);
    return Array.from(new Set([...fromSelected, ...fromText]));
  }, [idsText, selected]);

  const addProject = (item: ProjectSearchItem) => {
    setSelected((current) => (current.some((row) => row.id === item.id) ? current : [...current, item]));
  };

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const crore = budgetCrore.trim() === "" ? null : Number(budgetCrore);
      const body = await rankNeedImpact({
        project_ids: ids,
        available_budget_crore: crore == null || Number.isNaN(crore) ? null : crore,
        data_mode: mode,
      });
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ranking could not be completed.");
    } finally {
      setBusy(false);
    }
  };

  const compared = result ? result.items.length + result.unranked.length : ids.length;
  const withinBudget = result?.items.filter((item) => item.within_hypothetical_budget).length ?? 0;
  const proposedTotal = selected.reduce((sum, item) => sum + (item.allocation_amount ?? 0), 0);

  return (
    <div className="space-y-6">
      <PageHeader title="PROJECT PRIORITIZATION" explanation={FEATURE_EXPLANATIONS.need}>
        <p className="mt-1 text-sm font-medium text-[var(--navy)]">Need & Impact</p>
        <p className="mt-1 max-w-3xl text-sm text-[var(--muted)]">
          Compare proposed works to determine which should be considered first under the available budget and evidence.
        </p>
      </PageHeader>

      <DataModeBanner mode={mode} onModeChange={setMode} />
      <WorkflowStepper
        steps={["FIND PROJECTS", "COMPARE", "BUDGET", "PRIORITIZE"]}
        current={result ? 3 : ids.length ? 1 : 0}
      />

      <section className="svk-panel space-y-4 p-6">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">STEP 1 — FIND PROJECTS</h2>
        <p className="text-sm text-[var(--muted)]">Planning simulation. Search by Scheme ID, constituency, project type, or status.</p>
        <ProjectSelector mode={mode} onSelect={addProject} heading="+ ADD PROJECT" />
        <details className="text-sm">
          <summary className="cursor-pointer text-[var(--muted)]">Advanced ID entry</summary>
          <label className="mt-3 block text-sm">
            Candidate project ids
            <textarea
              className="svk-textarea mt-1"
              rows={3}
              value={idsText}
              onChange={(event) => setIdsText(event.target.value)}
              placeholder="e.g. 101, 102, 103"
            />
          </label>
        </details>
        <p className="text-sm font-semibold">PROJECTS COMPARED: {compared}</p>
        {selected.length ? (
          <div>
            <h3 className="text-sm font-semibold text-[var(--navy)]">SELECTED PROJECTS</h3>
            <ol className="mt-2 space-y-2">
              {selected.map((item) => (
                <li key={item.id} className="svk-card p-3 text-sm">
                  <p className="svk-mono font-semibold">{displayText(item.scheme_id)}</p>
                  <p>{displayText(item.work_description)}</p>
                  <p className="text-xs text-[var(--muted)]">
                    {displayText(item.constituency)} · {displayText(item.category)} · {formatAllocation(item.allocation_amount)}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </section>

      <section className="svk-panel space-y-3 p-6">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">STEP 2 — COMPARE</h2>
        <p className="text-sm">PROJECTS SELECTED: {ids.length}</p>
        <p className="text-sm text-[var(--muted)]">{DECISION_SUPPORT_ONLY}</p>
      </section>

      <section className="svk-panel space-y-3 p-6">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">STEP 3 — BUDGET</h2>
        <label className="block text-sm">
          Hypothetical available budget (₹ crore)
          <input className="svk-input mt-1" value={budgetCrore} onChange={(event) => setBudgetCrore(event.target.value)} />
        </label>
        <button type="button" className="svk-btn svk-btn-primary" onClick={() => void run()} disabled={busy || ids.length === 0}>
          {busy ? "Ranking…" : "Rank proposed works"}
        </button>
        {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      </section>

      {result ? (
        <section className="space-y-4">
          <h2 className="svk-display text-xl font-semibold">STEP 2 — COMPARISON</h2>
          <p className="text-sm">PROJECTS COMPARED: {result.items.length + result.unranked.length}</p>
          <div className="grid gap-3 sm:grid-cols-4">
            <BudgetMeter label="AVAILABLE BUDGET" value={result.available_budget} max={result.available_budget} />
            <BudgetMeter label="TOTAL PROPOSED" value={proposedTotal || null} max={result.available_budget} />
            <BudgetMeter label="PROJECTS COMPARED" value={result.items.length + result.unranked.length} max={result.items.length + result.unranked.length} />
            <BudgetMeter label="PROJECTS WITHIN BUDGET" value={withinBudget} max={result.items.length + result.unranked.length || 1} />
          </div>
          <p className="text-sm">{result.governance_note}</p>
          <p className="text-xs text-[var(--muted)]">{result.weight_note}</p>
          <p className="text-sm">{result.explanation}</p>
          {result.available_budget != null ? (
            <p className="text-sm">
              Available Budget: {result.available_budget.toLocaleString("en-IN")}
              {result.available_budget_crore != null ? ` (₹ ${result.available_budget_crore} crore, unit assumed)` : ""}.
              Projects compared: {result.items.length + result.unranked.length}. Projects within budget:{" "}
              {result.items.filter((item) => item.within_hypothetical_budget).length}. Total remaining after
              simulation:{" "}
              {result.remaining_budget == null ? "unavailable" : result.remaining_budget.toLocaleString("en-IN")}.
            </p>
          ) : null}
          <p className="text-xs text-[var(--muted)]">
            Automatic sanctioning: {String(result.automatic_sanction)}. This page has no sanction or payment action.
          </p>

          <div className="svk-table-wrap">
            <table className="svk-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Scheme ID</th>
                  <th>Project</th>
                  <th>Region</th>
                  <th>Project Type</th>
                  <th>Budget</th>
                  <th>Need</th>
                  <th>Impact</th>
                  <th>Urgency</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((item) => {
                  const selectedMatch = selected.find((row) => row.id === item.project_id);
                  return (
                    <tr key={item.project_id}>
                      <td>{item.rank}</td>
                      <td className="svk-mono">
                        <a className="underline" href={`/projects/${item.project_id}?mode=${mode === "REAL" ? "real" : "hybrid"}`}>
                          {selectedMatch?.scheme_id ?? `Project ${item.project_id}`}
                        </a>
                      </td>
                      <td>{displayText(selectedMatch?.work_description)}</td>
                      <td>{item.constituency}</td>
                      <td>{item.category}</td>
                      <td>{formatAllocation(item.requested_amount)}</td>
                      <td>{item.need_score ?? "INCONCLUSIVE"}</td>
                      <td>{item.impact_score ?? "INCONCLUSIVE"}</td>
                      <td>UNAVAILABLE</td>
                      <td>{item.priority_score ?? "INCONCLUSIVE"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">STEP 4 — PRIORITIZATION</h2>
          <p className="text-sm">{DECISION_SUPPORT_ONLY}</p>
          {result.items.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No work had both Need and Impact assessable, so ranking was not forced.
            </p>
          ) : (
            <ol className="space-y-3">
              {result.items.map((item) => {
                const selectedMatch = selected.find((row) => row.id === item.project_id);
                return (
                  <li key={`card-${item.project_id}`} className="svk-card p-5" data-tone="signal">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="svk-mono text-sm text-[var(--signal)]">Rank {item.rank}</p>
                        <p className="svk-mono font-semibold">{selectedMatch?.scheme_id ?? `Project ${item.project_id}`}</p>
                        <p className="text-sm">{displayText(selectedMatch?.work_description)}</p>
                        <p className="text-xs text-[var(--muted)]">
                          {item.constituency} · {formatAllocation(item.requested_amount)}
                        </p>
                      </div>
                      <StatusBadge value={item.priority_class} />
                    </div>
                    <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-4">
                      <div>
                        <dt className="text-xs text-[var(--muted)]">Need</dt>
                        <dd>{item.need_score ?? "INCONCLUSIVE"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-[var(--muted)]">Impact</dt>
                        <dd>{item.impact_score ?? "INCONCLUSIVE"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-[var(--muted)]">Urgency</dt>
                        <dd>UNAVAILABLE</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-[var(--muted)]">Priority</dt>
                        <dd>{item.priority_score ?? "INCONCLUSIVE"}</dd>
                      </div>
                    </dl>
                    <p className="mt-3 text-xs font-semibold tracking-[0.12em] text-[var(--navy)]">WHY THIS RANK</p>
                    <p className="mt-1 text-sm">{item.rationale}</p>
                    {item.why_ranked_above ? <p className="mt-1 text-xs">{item.why_ranked_above}</p> : null}
                    {item.why_ranked_below ? <p className="mt-1 text-xs">{item.why_ranked_below}</p> : null}
                    <p className="mt-2 text-xs">{budgetLabel(item.within_hypothetical_budget)}</p>
                    {item.budget_note ? <p className="mt-1 text-xs text-[var(--muted)]">{item.budget_note}</p> : null}
                  </li>
                );
              })}
            </ol>
          )}

          <h2 className="font-semibold text-[var(--navy)]">INCONCLUSIVE / not ranked</h2>
          {result.unranked.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No INCONCLUSIVE candidates.</p>
          ) : (
            <ul className="svk-panel space-y-2 p-4 text-sm">
              {result.unranked.map((item) => (
                <li key={`u-${item.project_id}`}>
                  Project {item.project_id} · {item.constituency} · {item.priority_class}. {item.rationale}
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </div>
  );
}
