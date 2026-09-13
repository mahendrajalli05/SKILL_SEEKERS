"use client";

import { useCallback, useEffect, useState } from "react";

import { checkSatellite, fetchSatellite } from "@/lib/api";
import type { DataMode, SatelliteResponse } from "@/lib/types";

function resultClass(result: string) {
  if (result === "SATELLITE_INCONSISTENT") {
    return "border-[var(--saffron)] bg-[#f8efe6]";
  }
  if (result === "SATELLITE_CONSISTENT") {
    return "border-[var(--navy)] bg-white";
  }
  return "border-[var(--line)] bg-[#f6f7f9]";
}

function yesNo(value: boolean | null | undefined) {
  if (value == null) return "unavailable";
  return value ? "Available" : "Unavailable";
}

export function SatellitePceBlock({ data }: { data: SatelliteResponse | null }) {
  if (!data?.plan_claim_evidence) {
    return null;
  }
  const pce = data.plan_claim_evidence;
  return (
    <section className={`space-y-2 border p-4 ${resultClass(data.overall_result)}`}>
      <h4 className="text-sm font-semibold text-[var(--navy)]">
        Satellite / remote sensing (Plan → Claim → Evidence)
      </h4>
      <p className="text-sm">CLAIM: {pce.claim ?? "The claimed work is present at the recorded project location."}</p>
      <p className="text-sm">SATELLITE: {pce.satellite}</p>
      <p className="text-sm font-medium">Result: {pce.result}</p>
      <p className="text-xs text-[var(--muted)]">{pce.note}</p>
      {pce.claim_marked_false ? null : (
        <p className="text-xs text-[var(--muted)]">The claim is not marked false automatically.</p>
      )}
    </section>
  );
}

export function SatelliteRemoteSensingPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [data, setData] = useState<SatelliteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scenario, setScenario] = useState("available");

  const load = useCallback(async () => {
    try {
      const body = await fetchSatellite(projectId, mode);
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Satellite evidence could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onCheck = async (useTestProvider: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const body = await checkSatellite(
        projectId,
        mode,
        useTestProvider
          ? { provider: "mock", testScenario: scenario }
          : { provider: "unavailable" },
      );
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Satellite check failed.");
    } finally {
      setBusy(false);
    }
  };

  const imageryAvailable = Boolean(data?.imagery_available);
  const showMap = Boolean(data?.map_available && data.official_imagery && imageryAvailable);

  return (
    <section className="space-y-4 svk-panel p-5">
      <div>
        <h2 className="text-xl font-semibold text-[var(--navy)]">Satellite / Remote Sensing</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Checks remote-sensing availability and consistency when imagery can be obtained.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Decision-support comparison with available remote-sensing imagery metadata. This does
          not determine legal wrongdoing, completion, or independently verified physical measurements.
        </p>
      </div>
      {data?.overall_result === "SATELLITE_UNAVAILABLE" ? (
        <div className="svk-unavailable rounded-lg border border-[var(--line)] p-6">
          <p className="text-sm font-semibold tracking-[0.12em] text-[var(--navy)]">SATELLITE UNAVAILABLE</p>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Live imagery is not currently configured for this project.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-4">
          <article className="svk-card p-4" data-tone="indigo">
            <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Provider</p>
            <p className="mt-1 font-medium">{data?.provider ?? "unavailable"}</p>
          </article>
          <article className="svk-card p-4" data-tone="indigo">
            <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Imagery status</p>
            <p className="mt-1 font-medium">{yesNo(data?.imagery_available)}</p>
          </article>
          <article className="svk-card p-4" data-tone="indigo">
            <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Date</p>
            <p className="mt-1 font-medium">{data?.acquisition_date ?? "unavailable"}</p>
          </article>
          <article className="svk-card p-4" data-tone="indigo">
            <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Result</p>
            <p className="mt-1 font-medium">{data?.overall_result ?? "Not assessed"}</p>
          </article>
        </div>
      )}
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          Provider: <span className="font-medium">{data?.provider ?? "unavailable"}</span>
        </div>
        <div>
          Imagery: <span className="font-medium">{yesNo(data?.imagery_available)}</span>
        </div>
        <div>
          Acquisition: <span className="font-medium">{data?.acquisition_date ?? "unavailable"}</span>
        </div>
        <div>
          Resolution:{" "}
          <span className="font-medium">
            {data?.spatial_resolution_m != null ? `${data.spatial_resolution_m} m` : "unavailable"}
          </span>
        </div>
        <div>
          Coverage: <span className="font-medium">{data?.coverage ?? "unavailable"}</span>
        </div>
        <div>
          Change: <span className="font-medium">{data?.change_result ?? "not assessed"}</span>
        </div>
        <div>
          Assessment: <span className="font-medium">{data?.overall_result ?? "Not assessed"}</span>
        </div>
        <div>
          Confidence:{" "}
          <span className="font-medium">
            {data ? `${data.confidence_label} (${Math.round(data.evidence_confidence * 100)}%)` : "unavailable"}
          </span>
        </div>
      </dl>
      {data?.labelled_synthetic || data?.data_mode === "HYBRID" || data?.data_mode === "SYNTHETIC" ? (
        <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
          {data.data_mode} — TEST/SYNTHETIC mocked imagery is not official satellite imagery
        </p>
      ) : null}
      <p className="text-sm">{data?.explanation}</p>
      {data?.resolution_analysis && data.resolution_analysis.sufficient === false ? (
        <p className="text-sm text-[var(--muted)]">
          Reason: {String(data.resolution_analysis.finding || "Resolution insufficient.")}
        </p>
      ) : null}
      <SatellitePceBlock data={data} />
      {showMap ? (
        <p className="text-sm">Official imagery coverage metadata is available for this check.</p>
      ) : (
        <p className="text-xs text-[var(--muted)]">
          No satellite map is shown because official imagery is not available.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={busy}
          className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
          onClick={() => void onCheck(false)}
        >
          Check available imagery
        </button>
        {mode !== "REAL" ? (
          <details className="text-sm">
            <summary className="cursor-pointer text-[var(--muted)]">Advanced TEST controls</summary>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <label className="text-sm">
                TEST scenario
                <select
                  className="svk-select mt-1"
                  value={scenario}
                  onChange={(event) => setScenario(event.target.value)}
                >
                  <option value="available">available</option>
                  <option value="unavailable">unavailable</option>
                  <option value="matching_location">matching location</option>
                  <option value="wrong_location">wrong location</option>
                  <option value="change_detected">before/after change</option>
                  <option value="no_change">no visible change</option>
                  <option value="insufficient_resolution">insufficient resolution</option>
                  <option value="wrong_date">wrong imagery date</option>
                </select>
              </label>
              <button
                type="button"
                disabled={busy}
                className="border border-[var(--saffron)] px-3 py-1.5 text-sm text-[var(--saffron)] disabled:opacity-50"
                onClick={() => void onCheck(true)}
              >
                Run TEST provider check
              </button>
            </div>
          </details>
        ) : null}
      </div>
      <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--muted)]">
        {(data?.limitations ?? []).slice(0, 6).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
