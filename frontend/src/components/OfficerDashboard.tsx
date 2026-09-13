"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { DataModeBanner } from "@/components/DataModeBanner";
import { MetricCard } from "@/components/system/MetricCard";
import { SvkIcon } from "@/components/system/SvkIcon";
import { HubTile, LifecycleChart } from "@/components/system/VisualKit";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { fetchHealth, fetchProjects, getApiBase } from "@/lib/api";
import { fetchPilotCounts, type PilotCounts } from "@/lib/dashboardStats";
import {
  DEFAULT_PILOT_STATE,
  displayText,
  formatAllocation,
  lifecycleFromStatus,
  parseDataMode,
  withModePath,
} from "@/lib/display";
import {
  DASHBOARD_WORKFLOWS,
  FEATURE_EXPLANATIONS,
  INTELLIGENCE_LAYERS,
  PRODUCT_LAYER,
  PRODUCT_NAME,
} from "@/lib/explanations";
import type { HealthResponse, ProjectSearchItem } from "@/lib/types";
import { SystemPipeline } from "@/components/system/SystemPipeline";

export function OfficerDashboard() {
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [counts, setCounts] = useState<PilotCounts | null>(null);
  const [recent, setRecent] = useState<ProjectSearchItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      fetchHealth(),
      fetchPilotCounts(mode),
      fetchProjects({
        page: 1,
        page_size: 8,
        state: DEFAULT_PILOT_STATE,
        apply_pilot_scope: true,
        mode: mode === "REAL" ? "real" : "hybrid",
      }).catch(() => null),
    ])
      .then(([healthBody, countBody, recentBody]) => {
        if (cancelled) return;
        setHealth(healthBody);
        setCounts(countBody);
        setRecent(recentBody?.items ?? []);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "API request failed");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  const unknown =
    counts?.total != null &&
    counts.future != null &&
    counts.ongoing != null &&
    counts.completed != null
      ? Math.max(0, counts.total - counts.future - counts.ongoing - counts.completed)
      : null;

  return (
    <div className="space-y-8">
      <header className="svk-reveal">
        <p className="svk-kicker">Andhra Pradesh Pilot</p>
        <h1 className="svk-display mt-1 text-[2rem] font-semibold text-[var(--navy)]">{PRODUCT_NAME}</h1>
        <p className="mt-1 text-sm font-medium tracking-[0.04em] text-[var(--navy)]">{PRODUCT_LAYER}</p>
        <p className="mt-1 text-sm text-[var(--muted)]">Andhra Pradesh Pilot</p>
      </header>

      <DataModeBanner mode={mode} />

      {error ? (
        <PageState
          kind="error"
          title="API Error"
          message={`Start the FastAPI server at ${getApiBase()} then refresh. ${error}`}
        />
      ) : null}

      {loading ? <PageState kind="loading" message="Loading officer dashboard…" /> : null}

      <section>
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">PROJECT LANDSCAPE</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard
            label="TOTAL PROJECTS"
            value={counts?.total == null ? "Unavailable" : counts.total.toLocaleString("en-IN")}
            hint={counts?.pilotLabel}
          />
          <MetricCard
            label="FUTURE"
            value={counts?.future == null ? "Unavailable" : counts.future.toLocaleString("en-IN")}
            tone="signal"
          />
          <MetricCard
            label="ONGOING"
            value={counts?.ongoing == null ? "Unavailable" : counts.ongoing.toLocaleString("en-IN")}
            tone="saffron"
          />
          <MetricCard
            label="COMPLETED"
            value={counts?.completed == null ? "Unavailable" : counts.completed.toLocaleString("en-IN")}
            tone="success"
          />
          <MetricCard
            label="UNKNOWN"
            value={unknown == null ? "Unavailable" : unknown.toLocaleString("en-IN")}
            tone="indigo"
          />
        </div>
        <div className="mt-4">
          <LifecycleChart
            future={counts?.future}
            ongoing={counts?.ongoing}
            completed={counts?.completed}
            unknown={unknown}
            total={counts?.total}
          />
        </div>
      </section>

      <section>
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">KEY WORKFLOWS</h2>
        <div className="svk-stagger mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {DASHBOARD_WORKFLOWS.map((item) => (
            <Link
              key={item.href}
              href={withModePath(item.href, mode)}
              className="svk-card group block p-5 hover:border-[var(--signal)]"
              data-tone="signal"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[var(--navy-soft)] text-[var(--navy-fill)]">
                <SvkIcon name={item.icon} />
              </div>
              <h3 className="mt-3 text-sm font-semibold tracking-[0.08em] text-[var(--navy)]">{item.title}</h3>
              <p className="mt-2 text-sm text-[var(--muted)]">{item.explanation}</p>
              <p className="mt-3 text-xs font-semibold tracking-[0.12em] text-[var(--signal)]">{item.action} →</p>
            </Link>
          ))}
        </div>
        <p className="mt-3 text-sm text-[var(--muted)]">
          High-priority ranking is assessed per work. There is no fleet-wide high-priority index in this prototype.
        </p>
      </section>

      <section>
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">INTELLIGENCE SYSTEM</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Project-level capabilities. This dashboard does not invent coverage percentages.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {INTELLIGENCE_LAYERS.map((layer) => (
            <HubTile
              key={layer.key}
              href={withModePath(layer.href, mode)}
              icon={layer.icon}
              title={layer.label}
              explanation={layer.explanation}
              tone={layer.tone}
            />
          ))}
        </div>
      </section>

      <section className="svk-panel p-5">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">SYSTEM FLOW</h2>
        <p className="mt-1 mb-4 text-sm text-[var(--muted)]">
          The officer path from discovery to a human decision.
        </p>
        <SystemPipeline />
      </section>

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">DISCOVERABLE PROJECTS</h2>
          <Link href={withModePath("/search", mode)} className="text-sm text-[var(--signal)]">
            All projects →
          </Link>
        </div>
        {recent.length === 0 ? (
          <PageState
            kind="empty"
            message="No project rows were returned for this dashboard sample. Use Search to open a work."
          />
        ) : (
          <div className="svk-table-wrap">
            <table className="svk-table svk-table-stack">
              <thead>
                <tr>
                  <th>Scheme ID</th>
                  <th>Project</th>
                  <th>Constituency</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Lifecycle</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recent.slice(0, 6).map((item) => (
                  <tr
                    key={item.id}
                    data-clickable="true"
                    onClick={() => {
                      window.location.href = withModePath(`/projects/${item.id}`, mode);
                    }}
                  >
                    <td data-label="Scheme ID" className="svk-mono font-medium">
                      {displayText(item.scheme_id)}
                    </td>
                    <td data-label="Project">
                      <Link href={withModePath(`/projects/${item.id}`, mode)} className="font-medium text-[var(--navy)]">
                        {displayText(item.work_description)}
                      </Link>
                    </td>
                    <td data-label="Constituency">{displayText(item.constituency)}</td>
                    <td data-label="Category">{displayText(item.category)}</td>
                    <td data-label="Amount">{formatAllocation(item.allocation_amount)}</td>
                    <td data-label="Lifecycle">
                      <StatusBadge value={lifecycleFromStatus(item.status)} />
                    </td>
                    <td data-label="Status">
                      <StatusBadge value={item.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">Unavailable fleet statistics</h2>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <UnavailableStat
            title="Investigation Priority distribution"
            message="A fleet-wide Investigation Priority distribution is not computed. Open a project to see its 0–100 review ranking. This dashboard does not assess every work."
          />
          <UnavailableStat
            title="Evidence Confidence"
            message="Evidence Confidence is computed per project. A dashboard-wide confidence statistic is unavailable."
          />
          <UnavailableStat
            title="Projects requiring review"
            message="A fleet-wide review queue is not available. Use Projects, then open the Investigation Workspace for a specific work."
          />
          <UnavailableStat
            title="Projects with insufficient evidence"
            message="Insufficient evidence is reported on each Project Digital Passport. This dashboard does not convert unknown values to zero."
          />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="API" value={health ? health.status : error ? "down" : "Unavailable"} />
        <MetricCard
          label="SQLite"
          value={health?.database.connected ? "connected" : error ? "unknown" : "Unavailable"}
        />
        <div className="svk-panel p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Current data mode</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusBadge kind={mode === "REAL" ? "REAL" : "HYBRID"} />
            {mode !== "REAL" ? <StatusBadge kind="SYNTHETIC" /> : null}
          </div>
        </div>
      </section>

      {health ? (
        <section className="svk-panel p-5 text-sm">
          <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">Governance</h2>
          <p className="mt-2">{health.governance.principle}</p>
          <p className="mt-1 text-[var(--muted)]">
            Outputs: {health.governance.outputs.join(", ")}. Does not output:{" "}
            {health.governance.does_not_output.join(", ")}.
          </p>
          <p className="mt-2 text-xs text-[var(--muted)]">{FEATURE_EXPLANATIONS.risk}</p>
          {mode === "HYBRID" ? (
            <p className="mt-2 text-sm text-[var(--saffron)]">
              Prototype/demo values may use synthetic enrichment.
            </p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function UnavailableStat({ title, message }: { title: string; message: string }) {
  return (
    <div className="svk-unavailable svk-panel p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{title}</p>
      <p className="mt-1 text-sm font-medium text-[var(--navy)]">Unavailable</p>
      <p className="mt-2 text-sm text-[var(--muted)]">{message}</p>
    </div>
  );
}
