"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

import { DemoCaseNotice } from "@/components/DemoCaseNotice";
import { DemoCaseSummary } from "@/components/DemoCaseSummary";
import { FieldRow } from "@/components/FieldRow";
import { InvestigationCopilotPanel } from "@/components/InvestigationCopilotPanel";
import { OfficerDecisionPanel } from "@/components/OfficerDecisionPanel";
import { ProjectLifecyclePanel } from "@/components/ProjectLifecyclePanel";
import { RiskFusionV2Panel } from "@/components/RiskFusionV2Panel";
import { WorkflowStepper } from "@/components/system/WorkflowStepper";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { fetchDemoCase, sendCopilotChat } from "@/lib/api";
import {
  SCHEME_ID_NOTE,
  formatAllocation,
  officerActionLabel,
  parseDataMode,
  recommendedActionLabel,
  withModePath,
} from "@/lib/display";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";
import type { CopilotChatResponse, DataMode, DemoCaseResponse, OfficerDecisionType } from "@/lib/types";

type OfficerMode = Exclude<DataMode, "SYNTHETIC">;

const STEPS = [
  "PROJECT",
  "PASSPORT",
  "LIFECYCLE",
  "INVESTIGATION",
  "EVIDENCE",
  "RISK",
  "COPILOT",
  "DECISION",
  "SUMMARY",
] as const;

const STEP_COPY: Record<(typeof STEPS)[number], string> = {
  PROJECT: "What this step demonstrates: the controlled hybrid project identity.",
  PASSPORT: "What this step demonstrates: the Project Digital Passport as the central record.",
  LIFECYCLE: "What this step demonstrates: FUTURE / ONGOING / COMPLETED workflow state.",
  INVESTIGATION: "What this step demonstrates: plan, claim, and investigation entry points.",
  EVIDENCE: "What this step demonstrates: stored Evidence Object IDs and labelled enrichment.",
  RISK: "What this step demonstrates: Investigation Priority and Evidence Confidence from Risk Fusion V2.",
  COPILOT: "What this step demonstrates: evidence-grounded questions, not scripted answers.",
  DECISION: "What this step demonstrates: the officer decision, not automatic payment.",
  SUMMARY: "What this step demonstrates: a case summary without forcing a fraud conclusion.",
};

function textValue(value: unknown) {
  if (value == null || value === "") return null;
  return String(value);
}

export function DemoCaseJourney() {
  const params = useParams<{ caseId: string }>();
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  const caseId = String(params.caseId || "");
  const [demo, setDemo] = useState<DemoCaseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const body = await fetchDemoCase(caseId, mode);
      setDemo(body);
      setError(null);
    } catch (err) {
      setDemo(null);
      setError(err instanceof Error ? err.message : "Demo case could not be loaded.");
    }
  }, [caseId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return <PageState kind="error" message={error} />;
  }
  if (!demo) {
    return <PageState kind="loading" message="Loading demo case…" />;
  }

  return <DemoCaseJourneyBody demo={demo} mode={mode} onReload={load} />;
}

function DemoCaseJourneyBody({
  demo,
  mode,
  onReload,
}: {
  demo: DemoCaseResponse;
  mode: OfficerMode;
  onReload: () => Promise<void>;
}) {
  const intel = useProjectIntelligence(demo.project_id, mode);
  const [copilotAnswer, setCopilotAnswer] = useState<CopilotChatResponse | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [step, setStep] = useState(0);
  const queryMode = mode === "REAL" ? "real" : "hybrid";
  const demoQuery = `mode=${queryMode}&demo=${demo.case_id.toLowerCase()}`;
  const passportHref = `/projects/${demo.project_id}?${demoQuery}`;
  const investigateHref = `/projects/${demo.project_id}/investigate?${demoQuery}`;
  const graphHref = `/projects/${demo.project_id}/graph?${demoQuery}`;
  const evidenceIds = demo.available_evidence.evidence_ids;
  const risk = demo.risk_fusion_v2;
  const enrichment =
    demo.available_plan.synthetic_enrichment && typeof demo.available_plan.synthetic_enrichment === "object"
      ? (demo.available_plan.synthetic_enrichment as Record<string, unknown>)
      : null;
  const current = STEPS[step];

  async function askCopilot(question: string) {
    setCopilotLoading(true);
    try {
      const response = await sendCopilotChat(demo.project_id, {
        question,
        data_mode: mode,
      });
      setCopilotAnswer(response);
    } finally {
      setCopilotLoading(false);
    }
  }

  async function onOfficerDecision(decisionType: OfficerDecisionType, reason: string) {
    await intel.recordDecision(decisionType, reason);
    await onReload();
  }

  async function onPlanningDecision(action: string, reason: string) {
    await intel.recordPlanningDecision(action, reason);
    await onReload();
  }

  return (
    <div className="space-y-6">
      <DemoCaseNotice caseName={`Demo case: ${demo.display_name}`} notice={demo.demo_notice} />

      <section className="svk-panel p-5">
        <h1 className="svk-display text-2xl font-semibold text-[var(--navy)]">{demo.display_name}</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">WHAT THIS STEP DEMONSTRATES</p>
        <p className="mt-1 text-sm">{STEP_COPY[current]}</p>
        <p className="mt-2 text-sm">{demo.short_description}</p>
        <p className="mt-2 text-sm text-[var(--saffron)]">CONTROLLED HYBRID DEMO — outcomes are not forced.</p>
      </section>

      <div className="overflow-x-auto">
        <WorkflowStepper steps={STEPS} current={step} onSelect={setStep} />
      </div>
      <div className="flex gap-2">
        <button type="button" className="svk-btn" disabled={step === 0} onClick={() => setStep((c) => Math.max(0, c - 1))}>
          Previous
        </button>
        <button
          type="button"
          className="svk-btn svk-btn-primary"
          disabled={step === STEPS.length - 1}
          onClick={() => setStep((c) => Math.min(STEPS.length - 1, c + 1))}
        >
          Next
        </button>
      </div>

      {current === "PROJECT" ? (
        <section id="project" className="svk-panel p-5">
          <h2 className="font-semibold text-[var(--navy)]">PROJECT</h2>
          <dl className="mt-3">
            <FieldRow label="SARVSAKSHI Scheme ID" value={demo.scheme_id} hint={SCHEME_ID_NOTE} />
            <FieldRow label="Internal Project ID" value={demo.internal_project_id} />
            <FieldRow label="Lifecycle" value={demo.lifecycle_state} />
            <FieldRow label="Source status" value={demo.source_status} />
            <FieldRow label="Data mode" value={demo.data_mode} />
            <FieldRow label="Constituency" value={demo.constituency} />
            <FieldRow label="Category" value={demo.category} />
            <FieldRow label="Requested amount" value={formatAllocation(demo.allocation_amount)} />
            <FieldRow label="Initial claim" value={demo.initial_claim} />
          </dl>
        </section>
      ) : null}

      {current === "PASSPORT" ? (
        <section id="passport" className="svk-panel p-5">
          <h2 className="font-semibold text-[var(--navy)]">PASSPORT</h2>
          <Link href={passportHref} className="svk-btn svk-btn-primary mt-4">
            Open Digital Passport
          </Link>
        </section>
      ) : null}

      {current === "LIFECYCLE" ? (
        <section id="lifecycle">
          <ProjectLifecyclePanel
            projectId={demo.project_id}
            mode={mode}
            lifecycle={intel.lifecycle.data ?? demo.lifecycle}
            loading={intel.lifecycle.loading}
            error={intel.lifecycle.error}
            submitting={intel.submitting}
            onPlanningDecision={demo.lifecycle_state === "FUTURE" ? onPlanningDecision : undefined}
          />
        </section>
      ) : null}

      {current === "INVESTIGATION" ? (
        <section className="svk-panel space-y-4 p-5">
          <h2 className="font-semibold text-[var(--navy)]">PLAN</h2>
          <h2 className="font-semibold text-[var(--navy)]">CLAIM</h2>
          <p className="text-sm">Claimant statement under evaluation. Not treated as an established fact.</p>
          <FieldRow label="Initial claim" value={demo.initial_claim} />
          <FieldRow label="PCE result" value={textValue(demo.pce?.overall_result)} />
          <div className="flex flex-wrap gap-2">
            <Link href={investigateHref} className="svk-btn svk-btn-primary">
              Open Investigation Workspace
            </Link>
            <Link href={graphHref} className="svk-btn">
              Open Relationship Graph
            </Link>
          </div>
        </section>
      ) : null}

      {current === "EVIDENCE" ? (
        <section id="evidence" className="svk-panel p-5">
          <h2 className="font-semibold text-[var(--navy)]">EVIDENCE</h2>
          {enrichment ? (
            <div className="mt-3 border border-[var(--saffron)] bg-[var(--saffron-soft)] p-3 text-sm">
              <p className="font-medium">SYNTHETIC enrichment (not official MPLADS)</p>
              <p className="mt-1">{textValue(enrichment.disclaimer)}</p>
            </div>
          ) : null}
          {evidenceIds.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--muted)]">No stored Evidence Object IDs for this mode.</p>
          ) : (
            <ul className="mt-3 space-y-1 break-all text-xs text-[var(--muted)]">
              {evidenceIds.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {current === "RISK" ? (
        <section id="risk">
          <RiskFusionV2Panel risk={intel.riskV2.data} loading={intel.riskV2.loading} error={intel.riskV2.error} />
          <p className="mt-2 text-xs text-[var(--muted)]">
            Risk Fusion V2 formula unchanged: {String(risk.formula_unchanged === true)}.
          </p>
        </section>
      ) : null}

      {current === "COPILOT" ? (
        <section id="copilot" className="space-y-4">
          <div className="svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">Suggested Copilot questions</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {demo.suggested_questions.map((question) => (
                <button
                  key={question}
                  type="button"
                  className="border border-[var(--line)] px-2 py-1 text-left text-xs text-[var(--navy)]"
                  disabled={copilotLoading}
                  onClick={() => void askCopilot(question)}
                >
                  {question}
                </button>
              ))}
            </div>
            {copilotAnswer ? (
              <div className="mt-4 text-sm">
                <p className="font-medium">{copilotAnswer.question}</p>
                <p className="mt-2 whitespace-pre-wrap">{copilotAnswer.answer}</p>
              </div>
            ) : null}
          </div>
          <InvestigationCopilotPanel projectId={demo.project_id} mode={mode} />
        </section>
      ) : null}

      {current === "DECISION" ? (
        <section id="decision">
          {demo.lifecycle_state === "FUTURE" ? (
            <div className="svk-panel p-5">
              <h2 className="font-semibold text-[var(--navy)]">Officer planning decision</h2>
              <p className="mt-2 text-sm">
                Last decision: {demo.officer_decision ? officerActionLabel(demo.officer_decision) : "Not recorded"}
              </p>
            </div>
          ) : (
            <OfficerDecisionPanel
              decisions={intel.decisions}
              submitting={intel.submitting}
              error={intel.decisionError}
              onSubmit={onOfficerDecision}
            />
          )}
        </section>
      ) : null}

      {current === "SUMMARY" ? <DemoCaseSummary summary={demo.final_case_summary} /> : null}

      <p className="text-sm text-[var(--muted)]">
        <Link href={withModePath("/demo", mode)} className="underline">
          Back to Demo Cases
        </Link>
      </p>
    </div>
  );
}
