"use client";

import { useEffect, useState } from "react";

import { fetchHealth, fetchProjects, getApiBase } from "@/lib/api";
import type { HealthResponse, ProjectListResponse } from "@/lib/types";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<ProjectListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchHealth(), fetchProjects()])
      .then(([healthBody, projectBody]) => {
        setHealth(healthBody);
        setProjects(projectBody);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "API request failed");
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--navy)]">Officer dashboard</h1>
        <p className="mt-1 text-[var(--muted)]">
          Foundation skeleton. No MPLADS rows are loaded until a real public
          extract is ingested.
        </p>
      </div>

      {error ? (
        <section className="border border-[var(--saffron)] bg-white p-4">
          <h2 className="font-semibold text-[var(--navy)]">API unreachable</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Start the FastAPI server at {getApiBase()} then refresh. {error}
          </p>
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3">
        <StatusCard
          label="API"
          value={health ? health.status : error ? "down" : "checking"}
        />
        <StatusCard
          label="SQLite"
          value={
            health?.database.connected
              ? "connected"
              : error
                ? "unknown"
                : "checking"
          }
        />
        <StatusCard label="Works loaded" value={String(projects?.total ?? 0)} />
      </section>

      <section className="border border-[var(--line)] bg-white p-5">
        <h2 className="font-semibold text-[var(--navy)]">Project list</h2>
        {projects && projects.total === 0 ? (
          <p className="mt-2 text-sm text-[var(--muted)]">{projects.note}</p>
        ) : (
          <p className="mt-2 text-sm text-[var(--muted)]">Waiting for API…</p>
        )}
      </section>

      {health ? (
        <section className="border border-[var(--line)] bg-white p-5 text-sm">
          <h2 className="font-semibold text-[var(--navy)]">Governance</h2>
          <p className="mt-2">{health.governance.principle}</p>
          <p className="mt-1 text-[var(--muted)]">
            Outputs: {health.governance.outputs.join(", ")}. Does not output:{" "}
            {health.governance.does_not_output.join(", ")}.
          </p>
          <p className="mt-1 text-[var(--muted)]">
            Database: {health.database.path} · tables{" "}
            {health.database.tables.length} · LLM{" "}
            {health.llm_enabled ? "enabled" : "disabled"}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-xl font-semibold text-[var(--navy)]">{value}</p>
    </div>
  );
}
