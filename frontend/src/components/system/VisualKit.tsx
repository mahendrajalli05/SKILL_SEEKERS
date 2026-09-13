import type { ReactNode } from "react";

import { SvkIcon, type IconName } from "@/components/system/SvkIcon";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function ToneDot({ tone = "signal" }: { tone?: "signal" | "violet" | "saffron" | "success" | "danger" | "indigo" }) {
  const fill =
    tone === "violet"
      ? "bg-[var(--violet)]"
      : tone === "saffron"
        ? "bg-[var(--saffron)]"
        : tone === "success"
          ? "bg-[var(--success)]"
          : tone === "danger"
            ? "bg-[var(--danger)]"
            : tone === "indigo"
              ? "bg-[var(--indigo)]"
              : "bg-[var(--signal)]";
  return <span className={`inline-block h-2 w-2 rounded-full ${fill}`} aria-hidden />;
}

export function LifecycleChart({
  future,
  ongoing,
  completed,
  unknown,
  total,
}: {
  future: number | null | undefined;
  ongoing: number | null | undefined;
  completed: number | null | undefined;
  unknown: number | null | undefined;
  total: number | null | undefined;
}) {
  const rows = [
    { label: "FUTURE", value: future, tone: "bg-[var(--signal)]" },
    { label: "ONGOING", value: ongoing, tone: "bg-[var(--saffron)]" },
    { label: "COMPLETED", value: completed, tone: "bg-[var(--success)]" },
    { label: "UNKNOWN", value: unknown, tone: "bg-[var(--indigo)]" },
  ];
  return (
    <div className="svk-panel p-5">
      <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">LIFECYCLE DISTRIBUTION</p>
      <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-[var(--navy-soft)]">
        {rows.map((row) => {
          const share = row.value != null && total ? Math.max(0, (row.value / total) * 100) : 0;
          return (
            <div
              key={row.label}
              className={`svk-score-fill ${row.tone}`}
              style={{ width: `${share}%` }}
              title={`${row.label} ${row.value ?? "Unavailable"}`}
            />
          );
        })}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        {rows.map((row) => {
          const share = row.value != null && total ? Math.round((row.value / total) * 100) : null;
          return (
            <div key={row.label}>
              <p className="text-[0.65rem] font-semibold tracking-[0.12em] text-[var(--muted)]">{row.label}</p>
              <p className="svk-mono mt-1 text-lg text-[var(--navy)]">
                {row.value == null ? "Unavailable" : row.value.toLocaleString("en-IN")}
              </p>
              <p className="text-xs text-[var(--muted)]">{share == null ? "Share unavailable" : `${share}% of observed total`}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ContributionBars({
  items,
}: {
  items: Array<{
    label: string;
    value: number | null | undefined;
    unavailable?: boolean;
    reason?: string | null;
  }>;
}) {
  return (
    <ul className="space-y-3">
      {items.map((item) => {
        const unavailable = item.unavailable || item.value == null;
        const width = unavailable ? 0 : Math.max(0, Math.min(100, item.value ?? 0));
        return (
          <li key={item.label}>
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="font-semibold tracking-[0.12em] text-[var(--navy)]">{item.label}</span>
              <span className="svk-mono text-[var(--muted)]">
                {unavailable ? "Unavailable" : item.value}
              </span>
            </div>
            <div className={`mt-1 h-2 overflow-hidden rounded-full ${unavailable ? "svk-unavailable" : "bg-[var(--navy-soft)]"}`}>
              {unavailable ? (
                <div className="h-full w-full border border-dashed border-[var(--line)]" />
              ) : (
                <div className="svk-score-fill h-full rounded-full bg-[var(--signal)]" style={{ width: `${width}%` }} />
              )}
            </div>
            {unavailable && item.reason ? (
              <p className="mt-1 text-[0.65rem] text-[var(--muted)]">{item.reason}</p>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

export function AnomalyScale({ score }: { score: number | null | undefined }) {
  if (score == null) {
    return (
      <div className="svk-unavailable rounded-md p-3 text-sm text-[var(--muted)]">
        Typical ←——————————→ Unusual
        <p className="mt-1 text-xs">Scale unavailable because no ML anomaly score was returned.</p>
      </div>
    );
  }
  return (
    <div>
      <div className="flex justify-between text-[0.65rem] font-semibold tracking-[0.12em] text-[var(--muted)]">
        <span>Typical</span>
        <span>Unusual</span>
      </div>
      <div className="relative mt-2 h-2 rounded-full bg-[linear-gradient(90deg,var(--success-soft),var(--saffron-soft),var(--violet-soft))]">
        <span
          className="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 border-white bg-[var(--violet)] shadow"
          style={{ left: `calc(${Math.max(0, Math.min(100, score))}% - 0.5rem)` }}
        />
      </div>
    </div>
  );
}

export function AnalysisPipeline({
  steps,
  activeIndex,
}: {
  steps: readonly string[];
  activeIndex?: number;
}) {
  return (
    <ol className="flex flex-col items-stretch gap-0">
      {steps.map((step, index) => {
        const active = activeIndex == null || index <= activeIndex;
        return (
          <li key={step} className="flex flex-col items-center">
            <div
              className={`min-w-[9rem] rounded-md border px-3 py-2 text-center ${
                active
                  ? "svk-pipeline-active border-[var(--violet)] bg-white text-[var(--navy)]"
                  : "border-[var(--line)] bg-[var(--surface-2)] text-[var(--muted)]"
              }`}
            >
              <p className="text-[0.68rem] font-semibold tracking-[0.14em]">{step}</p>
            </div>
            {index < steps.length - 1 ? (
              <span className="svk-pipeline-step py-1 text-[var(--muted)]" aria-hidden>
                ↓
              </span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

export function WorkflowCard({
  href,
  icon,
  title,
  explanation,
  action,
}: {
  href: string;
  icon: IconName;
  title: string;
  explanation: string;
  action: string;
}) {
  return (
    <a href={href} className="svk-card svk-panel group block p-5 transition hover:-translate-y-0.5 hover:border-[var(--signal)]">
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[var(--navy-soft)] text-[var(--navy-fill)]">
        <SvkIcon name={icon} className="h-4 w-4" />
      </div>
      <h3 className="mt-3 text-sm font-semibold tracking-[0.08em] text-[var(--navy)]">{title}</h3>
      <p className="mt-2 text-sm text-[var(--muted)]">{explanation}</p>
      <p className="mt-3 text-xs font-semibold tracking-[0.12em] text-[var(--signal)]">{action} →</p>
    </a>
  );
}

export function IdentityGrid({
  items,
}: {
  items: Array<{ label: string; value: ReactNode }>;
}) {
  return (
    <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="rounded-md bg-[var(--surface-2)] px-3 py-2">
          <dt className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">{item.label}</dt>
          <dd className="mt-1 text-sm font-medium text-[var(--navy)]">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function BudgetMeter({
  label,
  value,
  max,
}: {
  label: string;
  value: number | null | undefined;
  max: number | null | undefined;
}) {
  const width = value != null && max ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  return (
    <article className="svk-panel p-4">
      <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="svk-mono mt-2 text-2xl font-semibold text-[var(--navy)]">
        {value == null ? "Unavailable" : value.toLocaleString("en-IN")}
      </p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--navy-soft)]">
        <div className="svk-score-fill h-full bg-[var(--signal)]" style={{ width: `${width}%` }} />
      </div>
    </article>
  );
}

export function HubTile({
  href,
  icon,
  title,
  explanation,
  tone = "signal",
  availability = "Available",
}: {
  href: string;
  icon: IconName;
  title: string;
  explanation: string;
  tone?: "signal" | "violet" | "saffron" | "success" | "danger" | "indigo";
  availability?: string;
}) {
  return (
    <a href={href} className="svk-card block p-4 transition hover:-translate-y-0.5" data-tone={tone}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-[var(--navy-fill)]">
          <SvkIcon name={icon} />
        </span>
        <StatusBadge label={availability} />
      </div>
      <h3 className="mt-3 text-sm font-semibold text-[var(--navy)]">{title}</h3>
      <p className="mt-1 text-xs text-[var(--muted)]">{explanation}</p>
    </a>
  );
}
