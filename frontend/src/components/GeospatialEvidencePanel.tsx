"use client";

import { useCallback, useEffect, useState } from "react";

import { checkGeospatial, fetchGeospatial } from "@/lib/api";
import type { DataMode, GeospatialResponse } from "@/lib/types";
import { GeoMap } from "@/components/system/GeoMap";
import { FEATURE_EXPLANATIONS, GEO_PROTOTYPE_RULE } from "@/lib/explanations";
import { PageState } from "@/components/ui/PageState";

function metersText(value: number | null | undefined) {
  if (value == null) {
    return "unavailable";
  }
  return `${Math.round(value)} meters`;
}

function availability(available: boolean) {
  return available ? "Available" : "Unavailable";
}

function resultClass(result: string) {
  if (result === "LOCATION_MISMATCH") {
    return "border-[var(--saffron)] bg-[#f8efe6]";
  }
  if (result === "LOCATION_CONSISTENT") {
    return "border-[var(--navy)] bg-white";
  }
  return "border-[var(--line)] bg-[#f6f7f9]";
}

export function GeospatialPceBlock({ data }: { data: GeospatialResponse | null }) {
  if (!data) {
    return null;
  }
  const pce = data.plan_claim_evidence;
  return (
    <section className={`space-y-2 border p-4 ${resultClass(data.overall_result)}`}>
      <h4 className="text-sm font-semibold text-[var(--navy)]">Location consistency (Plan → Claim → Evidence)</h4>
      <p className="text-sm">
        CLAIM: {pce?.claim ?? "No site photograph claim was attached."}
      </p>
      <p className="text-sm">EVIDENCE: {pce?.evidence ?? "unavailable"}</p>
      <p className="text-sm font-medium">Result: {data.overall_result}</p>
      <p className="text-xs text-[var(--muted)]">
        {pce?.note ?? "Location consistency does not prove the photograph depicts the claimed work."}
      </p>
      {data.project_location.synthetic || data.data_mode === "HYBRID" || data.data_mode === "SYNTHETIC" ? (
        <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
          {data.data_mode} / SYNTHETIC project coordinates are not official MPLADS GPS
        </p>
      ) : null}
    </section>
  );
}

export function GeospatialEvidencePanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [data, setData] = useState<GeospatialResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await fetchGeospatial(projectId, mode);
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Geospatial evidence could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onCheck = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = await checkGeospatial(projectId, mode);
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Geospatial check failed.");
    } finally {
      setBusy(false);
    }
  };

  const projectAvailable = Boolean(data?.project_location.available);
  const gpsAvailable = (data?.summary.gps_available_count ?? 0) > 0;
  const distance = data?.images.find((item) => item.distance_meters != null)?.distance_meters ?? null;

  return (
    <section className="space-y-4 svk-panel p-5">
      <div>
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">GEOSPATIAL VERIFICATION</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">{FEATURE_EXPLANATIONS.geo}</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Location consistency between reported image GPS and the supplied project location when
          coordinates are actually available. This is not proof of authenticity or completion.
        </p>
        <p className="mt-2 text-xs text-[var(--muted)]">{GEO_PROTOTYPE_RULE}</p>
      </div>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      {!projectAvailable ? (
        <PageState
          kind="inconclusive"
          message="Verified coordinates are unavailable."
          compact
        />
      ) : (
          <GeoMap
          projectLat={data?.project_location.latitude ?? null}
          projectLng={data?.project_location.longitude ?? null}
          imageLat={data?.images.find((item) => item.location.latitude != null)?.location.latitude ?? null}
          imageLng={data?.images.find((item) => item.location.longitude != null)?.location.longitude ?? null}
          thresholdMeters={data?.threshold_meters ?? 500}
        />
      )}
      <div className="grid gap-3 sm:grid-cols-3">
        <article className="svk-card p-4" data-tone="indigo">
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">PROJECT LOCATION</p>
          <p className="mt-1 font-medium">{availability(projectAvailable)}</p>
        </article>
        <article className="svk-card p-4" data-tone="saffron">
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">IMAGE LOCATION</p>
          <p className="mt-1 font-medium">{availability(gpsAvailable)}</p>
        </article>
        <article className="svk-card p-4" data-tone={data?.overall_result === "LOCATION_MISMATCH" ? "danger" : "success"}>
          <p className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">RESULT</p>
          <p className="svk-mono mt-1 text-lg">{distance == null ? "—" : `${Math.round(distance)} m`}</p>
          <p className="text-xs text-[var(--muted)]">Threshold {data?.threshold_meters ?? 500} m</p>
          <p className="mt-1 text-sm font-semibold">{data?.overall_result ?? "Not assessed"}</p>
        </article>
      </div>
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          Project location:{" "}
          <span className="font-medium">{availability(projectAvailable)}</span>
          {data?.project_location.synthetic ? (
            <span className="ml-2 inline-block border border-[var(--saffron)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-[var(--saffron)]">
              SYNTHETIC
            </span>
          ) : null}
        </div>
        <div>
          Image GPS: <span className="font-medium">{availability(gpsAvailable)}</span>
        </div>
        <div>
          Distance: <span className="font-medium">{metersText(distance)}</span>
        </div>
        <div>
          Threshold:{" "}
          <span className="font-medium">{data?.threshold_meters ?? 500}m prototype threshold</span>
        </div>
        <div>
          Result: <span className="font-medium">{data?.overall_result ?? "Not assessed"}</span>
        </div>
        <div>
          Evidence confidence:{" "}
          <span className="font-medium">
            {data ? `${Math.round(data.evidence_confidence * 100)}%` : "unavailable"}
          </span>
        </div>
      </dl>
      {data?.data_mode === "HYBRID" || data?.data_mode === "SYNTHETIC" ? (
        <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
          {data.data_mode} — SYNTHETIC coordinates are not official MPLADS GPS
        </p>
      ) : null}
      <p className="text-sm">{data?.explanation}</p>
      <GeospatialPceBlock data={data} />
      {data?.summary.mixed_results ? (
        <p className="text-sm text-[var(--muted)]">
          One matching image does not make every other image trustworthy.
        </p>
      ) : null}
      <ul className="space-y-2 text-sm">
        {(data?.images ?? []).map((item) => (
          <li key={item.image_id} className="border border-[var(--line)] p-3">
            Image {item.image_id}: {item.result}
            {item.distance_meters != null ? ` · ${metersText(item.distance_meters)}` : " · GPS unavailable"}
            {item.location.data_mode === "HYBRID" || item.location.data_mode === "SYNTHETIC" ? (
              <span className="ml-2 text-[10px] uppercase text-[var(--saffron)]">{item.location.data_mode}</span>
            ) : null}
          </li>
        ))}
      </ul>
      <p className="text-xs text-[var(--muted)]">
        Satellite verification: {data?.satellite.result ?? "SATELLITE_VERIFICATION_NOT_AVAILABLE"}
      </p>
      <button
        type="button"
        disabled={busy}
        className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
        onClick={() => void onCheck()}
      >
        Run location check
      </button>
      <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--muted)]">
        {(data?.limitations ?? []).slice(0, 6).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
