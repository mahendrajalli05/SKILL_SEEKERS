"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { DemoCaseNotice } from "@/components/DemoCaseNotice";
import { PageHeader } from "@/components/system/PageHeader";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { fetchDemoCases } from "@/lib/api";
import { parseDataMode, withModePath } from "@/lib/display";
import type { DemoCaseListResponse } from "@/lib/types";

export function DemoCaseLaunch() {
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  const [data, setData] = useState<DemoCaseListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchDemoCases(mode)
      .then((body) => {
        if (!cancelled) {
          setData(body);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Demo cases could not be loaded.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Controlled hybrid demo"
        title="SARVSAKSHI DEMO CENTER"
        explanation={FEATURE_EXPLANATIONS.demo}
      >
        <p className="mt-1 text-[var(--muted)]">
          Follow a project from discovery to investigation and officer decision.
        </p>
        <p className="sr-only">Demo Cases</p>
      </PageHeader>
      <DemoCaseNotice notice={data?.demo_notice} />
      {error ? <PageState kind="error" message={error} /> : null}
      {!data && !error ? <PageState kind="loading" message="Loading demo cases…" /> : null}
      {data ? (
        <div className="grid gap-4 md:grid-cols-2">
          {data.items.map((item) => (
            <article key={item.case_id} className="svk-panel p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="svk-display text-lg font-semibold text-[var(--navy)]">{item.display_name}</h2>
                <StatusBadge kind="DEMO" />
                <StatusBadge kind="HYBRID" />
                {item.lifecycle_state ? <StatusBadge value={item.lifecycle_state} /> : null}
              </div>
              <p className="mt-1 text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--saffron)]">
                CONTROLLED HYBRID DEMO
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">{item.purpose}</p>
              <p className="mt-2 text-sm">{item.short_description}</p>
              <p className="mt-3 grid gap-1 text-xs text-[var(--muted)]">
                <span>Scenario: {item.purpose}</span>
                <span>Lifecycle: {item.lifecycle_state ?? item.expected_lifecycle}</span>
                <span>Primary concern: {item.expected_direction}</span>
                <span>Evidence: recorded on the investigation journey</span>
              </p>
              <p className="mt-2 text-xs text-[var(--muted)]">
                This is not confirmed fraud, guaranteed safety, or an official finding.
              </p>
              {item.available ? (
                <Link href={withModePath(item.href, mode)} className="svk-btn svk-btn-primary mt-4">
                  START INVESTIGATION → Open {item.display_name}
                </Link>
              ) : (
                <p className="mt-4 text-sm text-[var(--saffron)]">
                  Controlled project is not loaded in this database.
                </p>
              )}
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
