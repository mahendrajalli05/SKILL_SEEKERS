"use client";

import { FormEvent, useState } from "react";

import { DataModeBanner } from "@/components/DataModeBanner";
import { MLSignalPanel } from "@/components/system/MLSignalPanel";
import { PageHeader } from "@/components/system/PageHeader";
import { AnalysisPipeline } from "@/components/system/VisualKit";
import { WorkflowStepper } from "@/components/system/WorkflowStepper";
import { PageState } from "@/components/ui/PageState";
import { assessNewProject } from "@/lib/api";
import { FEATURE_EXPLANATIONS, ML_NOT_FRAUD } from "@/lib/explanations";
import type { DataMode, NewProjectAssessResponse } from "@/lib/types";

function text(value: unknown): string {
  if (value == null) {
    return "—";
  }
  return String(value);
}

const STEPS = ["PROJECT", "PROPOSAL", "CONTEXT", "ASSESS"];
const ANALYSIS = ["INPUT", "COST", "ML", "OVERLAP", "COMPLIANCE", "CONTEXT", "ASSESSMENT"];

export default function AssessNewProjectPage() {
  const [step, setStep] = useState(0);
  const [mode, setMode] = useState<DataMode>("REAL");
  const [state, setState] = useState("Andhra Pradesh");
  const [constituency, setConstituency] = useState("KURNOOL");
  const [category, setCategory] = useState("Normal/Others");
  const [house, setHouse] = useState("");
  const [status, setStatus] = useState("");
  const [work, setWork] = useState("Construction of water tanks");
  const [amount, setAmount] = useState("250000");
  const [recDate, setRecDate] = useState("2023-06-01");
  const [result, setResult] = useState<NewProjectAssessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const parsed = Number(amount);
      const body = await assessNewProject({
        state,
        constituency,
        category,
        work_description: work,
        allocation_amount: Number.isFinite(parsed) ? parsed : null,
        recommendation_date: recDate || null,
        status: status || undefined,
        house: house || undefined,
        data_mode: mode,
      });
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assessment could not be completed.");
    } finally {
      setBusy(false);
    }
  };

  const costMl = result?.ml.cost;
  const costPeer = result?.cost_v1_1;

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="NEW PROJECT ASSESSMENT"
        title="ASSESS A NEW PROJECT"
        explanation={FEATURE_EXPLANATIONS.assessment}
      >
        <p className="mt-1 max-w-3xl text-sm text-[var(--muted)]">
          Functional assessment of a proposed work that does not yet have a stored project id.
          Isolation Forest is an additional unsupervised signal. Cost Intelligence V1.1 remains the
          interpretable peer baseline. Not a fraud probability, sanction, or payment release.
        </p>
      </PageHeader>

      <DataModeBanner mode={mode} onModeChange={setMode} />
      <WorkflowStepper steps={STEPS} current={step} onSelect={setStep} />

      <form className="svk-panel space-y-5 p-6" onSubmit={onSubmit}>
        {step === 0 ? (
          <section className="space-y-4">
            <h2 className="svk-display text-xl font-semibold">STEP 1 — PROJECT IDENTITY</h2>
            <p className="text-sm text-[var(--muted)]">Supported fields only. MP is not a stored assessment field.</p>
            <label className="block text-sm">
              State
              <input className="svk-input mt-1" value={state} onChange={(e) => setState(e.target.value)} />
            </label>
            <label className="block text-sm">
              Constituency
              <input className="svk-input mt-1" value={constituency} onChange={(e) => setConstituency(e.target.value)} />
            </label>
            <label className="block text-sm">
              Category
              <input className="svk-input mt-1" value={category} onChange={(e) => setCategory(e.target.value)} />
            </label>
            <label className="block text-sm">
              House
              <input className="svk-input mt-1" value={house} onChange={(e) => setHouse(e.target.value)} placeholder="Optional" />
            </label>
            <label className="block text-sm">
              Status
              <input className="svk-input mt-1" value={status} onChange={(e) => setStatus(e.target.value)} placeholder="Optional where supported" />
            </label>
          </section>
        ) : null}
        {step === 1 ? (
          <section className="space-y-4">
            <h2 className="svk-display text-xl font-semibold">STEP 2 — PROJECT PROPOSAL</h2>
            <label className="block text-sm">
              Work description
              <textarea className="svk-textarea mt-1" rows={4} value={work} onChange={(e) => setWork(e.target.value)} />
            </label>
            <label className="block text-sm">
              Estimated allocation
              <input className="svk-input mt-1" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </label>
            <label className="block text-sm">
              Recommendation date
              <input className="svk-input mt-1" type="date" value={recDate} onChange={(e) => setRecDate(e.target.value)} />
            </label>
          </section>
        ) : null}
        {step === 2 ? (
          <section className="space-y-3">
            <h2 className="svk-display text-xl font-semibold">STEP 3 — CONTEXT</h2>
            <p className="text-sm text-[var(--muted)]">
              Contextual intelligence uses verified external public indicators after assessment. Regional
              statistics are not project-specific beneficiary counts.
            </p>
            <PageState
              kind="unavailable"
              message="External context is retrieved during assessment when a supported geography is present. No additional context fields are accepted on this form."
              compact
            />
          </section>
        ) : null}
        {step === 3 ? (
          <section className="space-y-4">
            <h2 className="svk-display text-xl font-semibold">STEP 4 — RUN ASSESSMENT</h2>
            <p className="text-sm text-[var(--muted)]">
              {state} · {constituency} · {category} · {work}
            </p>
            {busy ? <AnalysisPipeline steps={ANALYSIS} activeIndex={6} /> : null}
          </section>
        ) : null}
        <div className="flex gap-2">
          <button type="button" className="svk-btn" disabled={step === 0} onClick={() => setStep((c) => Math.max(0, c - 1))}>
            Previous
          </button>
          {step < 3 ? (
            <button type="button" className="svk-btn svk-btn-primary" onClick={() => setStep((c) => Math.min(3, c + 1))}>
              Next
            </button>
          ) : null}
          <button className="svk-btn svk-btn-primary" type="submit" disabled={busy}>
            {busy ? "Assessing…" : step === 3 ? "RUN ASSESSMENT" : "Assess"}
          </button>
        </div>
      </form>

      {error ? <p className="text-sm text-red-800">{error}</p> : null}

      {result ? (
        <div className="space-y-4">
          <section className="svk-panel p-5">
            <p className="svk-kicker">NEW PROJECT ASSESSMENT</p>
            <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">ASSESSMENT RESULT</h2>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5 text-sm">
              <div>
                <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Project</dt>
                <dd>{work}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Constituency</dt>
                <dd>{constituency}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Type</dt>
                <dd>{category}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Proposed amount</dt>
                <dd>{amount}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Recommendation date</dt>
                <dd>{recDate || "—"}</dd>
              </div>
            </dl>
          </section>
          <section className="svk-card p-5" data-tone="signal">
            <h2 className="font-semibold text-[var(--navy)]">COST INTELLIGENCE</h2>
            <p className="text-sm">Cost signal (V1.1)</p>
            <p className="svk-mono mt-2 text-3xl font-semibold text-[var(--signal)]">{text(costPeer?.cost_anomaly_score)}</p>
            <p className="text-sm">Outcome: {text(costPeer?.outcome)}</p>
            <p className="mt-2 text-sm">{text(costPeer?.explanation)}</p>
          </section>
          <MLSignalPanel signal={costMl} />
          <section className="svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">OVERLAP</h2>
            <p className="text-sm">Overlap signal</p>
            <p className="text-sm">Outcome: {text(result.overlap_v1?.outcome)}</p>
            <p className="mt-2 text-sm">{text(result.overlap_v1?.explanation)}</p>
          </section>
          <section className="svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">Compliance</h2>
            <p className="text-sm">Status: {text(result.compliance_v1?.status)}</p>
            <p className="mt-2 text-sm">{text(result.compliance_v1?.explanation)}</p>
          </section>
          <section className="svk-unavailable svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">Investigation Priority</h2>
            <p className="text-sm">
              {result.risk_fusion_v2.available
                ? text(result.risk_fusion_v2.investigation_priority)
                : result.risk_fusion_v2.reason}
            </p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Risk Fusion V2 is not generated for a truly new project when historical evidence is unavailable.
            </p>
          </section>
          {result.contextual_v1 ? (
            <section className="svk-panel p-5">
              <h2 className="font-semibold text-[var(--navy)]">CONTEXTUAL INTELLIGENCE</h2>
              <p className="text-sm">{result.contextual_v1.assessment_kind || "NEW_PROJECT_ASSESSMENT"}</p>
              <p className="mt-1 text-sm">{result.contextual_v1.governance_note}</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                External context is not historical Evidence, expenditure, or project-specific beneficiaries.
              </p>
            </section>
          ) : null}
          <section className="svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">DATA AVAILABILITY</h2>
            <p className="text-sm">Training mode: {text(costMl?.training_mode)}</p>
            <p className="text-sm">Data hash: {text(costMl?.training_data_hash)}</p>
            <p className="text-sm">Coverage: {text(costMl?.feature_availability.coverage)}</p>
            <ul className="mt-2 list-disc pl-5 text-sm text-[var(--muted)]">
              {result.limitations.slice(0, 6).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="mt-2 text-xs">
              Automatic sanction: {String(result.automatic_sanction)} · Automatic payment:{" "}
              {String(result.automatic_payment)}. {ML_NOT_FRAUD}
            </p>
          </section>
          <section className="svk-unavailable svk-panel p-5">
            <h2 className="font-semibold text-[var(--navy)]">NEED & IMPACT</h2>
            <p className="text-sm">UNAVAILABLE</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Need & Impact is not returned by new-project assessment. Open Planning after a project is stored.
            </p>
          </section>
          <section className="svk-card p-5" data-tone="saffron">
            <h2 className="font-semibold text-[var(--navy)]">ASSESSMENT SUMMARY</h2>
            <p className="mt-1 text-sm">
              {result.assessment_kind || "NEW PROJECT ASSESSMENT"} — this is not stored
              project evidence (PROJECT_STORED_EVIDENCE). No historical Evidence Objects
              were created. No historical project evidence has been created.
            </p>
            <p className="mt-2 text-sm font-medium">No historical project evidence exists yet.</p>
            <p className="mt-2 text-xs text-[var(--muted)]">{ML_NOT_FRAUD}</p>
          </section>
        </div>
      ) : null}
    </div>
  );
}
