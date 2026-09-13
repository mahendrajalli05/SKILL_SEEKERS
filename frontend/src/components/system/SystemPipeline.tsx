import { SvkIcon } from "@/components/system/SvkIcon";
import { SYSTEM_PIPELINE, SYSTEM_PIPELINE_NODES } from "@/lib/explanations";

export function SystemPipeline({
  steps = SYSTEM_PIPELINE,
}: {
  steps?: readonly string[];
}) {
  const nodes = steps.map((step) => SYSTEM_PIPELINE_NODES.find((node) => node.title === step) ?? {
    title: step,
    explanation: "",
    icon: "analyse" as const,
  });
  return (
    <ol className="flex flex-wrap items-stretch gap-2">
      {nodes.map((node, index) => (
        <li key={node.title} className="svk-reveal flex min-w-[8.5rem] flex-1 items-center gap-2">
          <div className="flex-1 rounded-lg border border-[var(--line)] bg-white px-3 py-3 text-center shadow-sm">
            <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-[var(--navy-soft)] text-[var(--navy-fill)]">
              <SvkIcon name={node.icon} className="h-4 w-4" />
            </div>
            <p className="mt-2 text-[0.68rem] font-semibold tracking-[0.14em] text-[var(--navy)]">{node.title}</p>
            {node.explanation ? <p className="mt-1 text-xs text-[var(--muted)]">{node.explanation}</p> : null}
          </div>
          {index < nodes.length - 1 ? (
            <span className="svk-pipeline-step hidden text-[var(--muted)] sm:block" aria-hidden>
              →
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export function OfficerPipeline() {
  return <SystemPipeline steps={["PROJECT", "INTELLIGENCE", "EVIDENCE", "RISK", "INVESTIGATION", "OFFICER DECISION"]} />;
}

export function PceChain() {
  const steps = ["PLAN", "CLAIM", "EVIDENCE", "RESULT"];
  return (
    <ol className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
      {steps.map((step, index) => (
        <li key={step} className="flex items-center gap-2">
          <span className="rounded-md border border-[var(--line)] bg-white px-3 py-1.5 text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--navy)] shadow-sm">
            {step}
          </span>
          {index < steps.length - 1 ? (
            <span className="svk-pipeline-step text-[var(--muted)]" aria-hidden>
              →
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export function InvestigationFlow() {
  const steps = ["QUESTION", "EVIDENCE", "SIGNALS", "RELATIONSHIPS", "ASSESSMENT", "DECISION"];
  return (
    <ol className="flex flex-wrap items-center gap-2 text-[0.65rem] font-semibold tracking-[0.12em] text-[var(--muted)]">
      {steps.map((step, index) => (
        <li key={step} className="flex items-center gap-2">
          <span>{step}</span>
          {index < steps.length - 1 ? <span aria-hidden>→</span> : null}
        </li>
      ))}
    </ol>
  );
}
