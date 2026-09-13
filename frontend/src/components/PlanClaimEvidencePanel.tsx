"use client";

import { useCallback, useEffect, useState } from "react";

import { FieldRow } from "@/components/FieldRow";
import { GeospatialPceBlock } from "@/components/GeospatialEvidencePanel";
import { ImageForensicsPceBlock } from "@/components/ImageForensicsPanel";
import { SatellitePceBlock } from "@/components/SatelliteRemoteSensingPanel";
import {
  attachEvidence,
  checkGeospatial,
  fetchClaims,
  fetchGeospatial,
  fetchImageForensics,
  fetchSatellite,
  fetchPlan,
  fetchProjectImages,
  fetchVerification,
  saveClaim,
  savePlan,
} from "@/lib/api";
import { UNAVAILABLE_REAL_LABEL } from "@/lib/display";
import type {
  ClaimRead,
  ConsistencyResult,
  DataMode,
  EvidenceAttachment,
  GeospatialResponse,
  ImageForensicsResponse,
  SatelliteResponse,
  PlanField,
  PlanRead,
  VerificationRead,
} from "@/lib/types";

const TABS = ["PLAN", "CLAIM", "EVIDENCE", "RESULT"] as const;
type Tab = (typeof TABS)[number];

function resultClass(result: string) {
  if (result === "MISMATCH") {
    return "border-[var(--saffron)] bg-[#f8efe6]";
  }
  if (result === "CONSISTENT") {
    return "border-[var(--navy)] bg-white";
  }
  return "border-[var(--line)] bg-[#f6f7f9]";
}

function formatFieldValue(field: PlanField): string {
  if (!field.available || field.value == null || field.value === "") {
    return UNAVAILABLE_REAL_LABEL;
  }
  return String(field.value);
}

export function VerificationResultBlock({ result }: { result: VerificationRead }) {
  return (
    <section className={`space-y-4 border p-5 ${resultClass(result.overall_result)}`}>
      <div>
        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Overall result</p>
        <p className="text-2xl font-semibold text-[var(--navy)]">{result.overall_result}</p>
        <p className="mt-1 text-sm">
          Evidence confidence: {Math.round(result.evidence_confidence * 100)} / 100
        </p>
      </div>
      <p className="text-sm">{result.explanation}</p>
      <div className="grid gap-4 lg:grid-cols-3">
        <article>
          <h4 className="text-sm font-semibold text-[var(--navy)]">Plan findings</h4>
          <ul className="mt-2 space-y-1 text-sm">
            {result.plan_findings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article>
          <h4 className="text-sm font-semibold text-[var(--navy)]">Claim findings</h4>
          <ul className="mt-2 space-y-1 text-sm">
            {result.claim_findings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article>
          <h4 className="text-sm font-semibold text-[var(--navy)]">Evidence findings</h4>
          <ul className="mt-2 space-y-1 text-sm">
            {result.evidence_findings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
      {result.mismatches.length > 0 ? (
        <div>
          <h4 className="text-sm font-semibold text-[var(--navy)]">Mismatches</h4>
          <ul className="mt-2 space-y-2 text-sm">
            {result.mismatches.map((item) => (
              <li key={item.comparison_id} className="border border-[var(--line)] bg-white p-3">
                {item.pair}: {item.explanation}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div>
        <h4 className="text-sm font-semibold text-[var(--navy)]">Missing information</h4>
        {result.missing_information.length === 0 ? (
          <p className="mt-2 text-sm text-[var(--muted)]">No missing-information items were listed.</p>
        ) : (
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {result.missing_information.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-xs text-[var(--muted)]">{result.note}</p>
    </section>
  );
}

export function PlanClaimEvidencePanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [tab, setTab] = useState<Tab>("PLAN");
  const [plan, setPlan] = useState<PlanRead | null>(null);
  const [claims, setClaims] = useState<ClaimRead[]>([]);
  const [attachments, setAttachments] = useState<EvidenceAttachment[]>([]);
  const [result, setResult] = useState<VerificationRead | null>(null);
  const [geo, setGeo] = useState<GeospatialResponse | null>(null);
  const [satellite, setSatellite] = useState<SatelliteResponse | null>(null);
  const [forensics, setForensics] = useState<ImageForensicsResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [scope, setScope] = useState("");
  const [budget, setBudget] = useState("");
  const [dimensions, setDimensions] = useState("");
  const [dimensionsUnit, setDimensionsUnit] = useState("sq.ft");
  const [milestoneAmount, setMilestoneAmount] = useState("");
  const [progress, setProgress] = useState("");
  const [expenditure, setExpenditure] = useState("");
  const [completion, setCompletion] = useState("");
  const [quantity, setQuantity] = useState("");
  const [quantityUnit, setQuantityUnit] = useState("sq.ft");
  const [documentType, setDocumentType] = useState("pdf");
  const [filename, setFilename] = useState("");
  const [observedQuantity, setObservedQuantity] = useState("");
  const [observedExpenditure, setObservedExpenditure] = useState("");

  const load = useCallback(async () => {
    try {
      const [planBody, claimBody] = await Promise.all([
        fetchPlan(projectId, mode),
        fetchClaims(projectId, mode),
      ]);
      setPlan(planBody);
      setClaims(claimBody.items);
      setScope(planBody.sanctioned_scope ?? "");
      setBudget(planBody.budget_estimate == null ? "" : String(planBody.budget_estimate));
      setDimensions(planBody.dimensions_value == null ? "" : String(planBody.dimensions_value));
      if (planBody.dimensions_unit) setDimensionsUnit(planBody.dimensions_unit);
      setMilestoneAmount(planBody.milestone_amount == null ? "" : String(planBody.milestone_amount));
      try {
        const geoBody = await fetchGeospatial(projectId, mode);
        if (geoBody.overall_result) {
          setGeo(geoBody);
        }
      } catch {
        setGeo(null);
      }
      try {
        const satelliteBody = await fetchSatellite(projectId, mode);
        if (satelliteBody.overall_result) {
          setSatellite(satelliteBody);
        }
      } catch {
        setSatellite(null);
      }
      try {
        const listed = await fetchProjectImages(projectId, mode);
        const forensicItems: ImageForensicsResponse[] = [];
        for (const image of listed.items.slice(0, 8)) {
          try {
            const body = await fetchImageForensics(image.image_id, mode);
            if (body.overall_assessment) {
              forensicItems.push(body);
            }
          } catch {
            /* forensic framing is optional in the Evidence section */
          }
        }
        setForensics(forensicItems);
      } catch {
        setForensics([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan–Claim–Evidence could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const numberOrNull = (value: string) => {
    const text = value.trim();
    if (!text) return null;
    const parsed = Number(text);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const onSavePlan = async () => {
    setBusy(true);
    setError(null);
    try {
      const saved = await savePlan(projectId, {
        sanctioned_scope: scope || null,
        budget_estimate: numberOrNull(budget),
        dimensions_value: numberOrNull(dimensions),
        dimensions_unit: dimensionsUnit || null,
        milestone_amount: numberOrNull(milestoneAmount),
        source: "officer_recorded",
        data_mode: mode,
      });
      setPlan(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan could not be stored.");
    } finally {
      setBusy(false);
    }
  };

  const onSaveClaim = async () => {
    setBusy(true);
    setError(null);
    try {
      const saved = await saveClaim(projectId, {
        claimed_progress_percent: numberOrNull(progress),
        claimed_expenditure: numberOrNull(expenditure),
        claimed_completion_state: completion || null,
        claimed_quantity: numberOrNull(quantity),
        claimed_quantity_unit: quantityUnit || null,
        claimant_source: "implementing_agency",
        data_mode: mode,
      });
      setClaims((current) => [saved, ...current]);
      setTab("EVIDENCE");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim could not be stored.");
    } finally {
      setBusy(false);
    }
  };

  const onAttach = async () => {
    setBusy(true);
    setError(null);
    try {
      const saved = await attachEvidence(projectId, {
        document_type: documentType,
        filename: filename || (documentType === "image" ? "site.jpg" : "supporting.pdf"),
        observed_quantity: numberOrNull(observedQuantity),
        observed_quantity_unit: numberOrNull(observedQuantity) != null ? quantityUnit : null,
        observed_expenditure: numberOrNull(observedExpenditure),
        source: "officer_upload",
        data_mode: mode,
      });
      setAttachments((current) => [saved, ...current]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evidence could not be attached.");
    } finally {
      setBusy(false);
    }
  };

  const onVerify = async () => {
    setBusy(true);
    setError(null);
    try {
      const verified = await fetchVerification(projectId, mode);
      setResult(verified);
      setTab("RESULT");
      try {
        const geoBody = await checkGeospatial(projectId, mode);
        setGeo(geoBody);
      } catch {
        /* geospatial remains optional alongside PCE verification */
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification could not be run.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section id="plan-claim-evidence" className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="text-xl font-semibold text-[var(--navy)]">Plan → Claim → Evidence</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Compare what was planned, what was claimed, and what evidence was attached.
          Results are CONSISTENT, MISMATCH, or INCONCLUSIVE. This is not a legal finding.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {TABS.map((item) => (
          <button
            key={item}
            type="button"
            className={`border px-3 py-1.5 text-sm ${
              tab === item ? "border-[var(--navy)] bg-[var(--navy)] text-white" : "border-[var(--line)]"
            }`}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}

      {tab === "PLAN" ? (
        <div className="space-y-4">
          <dl>
            {(plan?.fields ?? []).map((field) => (
              <FieldRow
                key={field.name}
                label={field.name.replaceAll("_", " ")}
                value={formatFieldValue(field)}
                hint={field.available ? field.source : field.unavailable_reason ?? undefined}
                synthetic={field.synthetic}
              />
            ))}
          </dl>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              Sanctioned scope
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={scope} onChange={(e) => setScope(e.target.value)} />
            </label>
            <label className="text-sm">
              Budget / estimate
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={budget} onChange={(e) => setBudget(e.target.value)} />
            </label>
            <label className="text-sm">
              Dimensions
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={dimensions} onChange={(e) => setDimensions(e.target.value)} />
            </label>
            <label className="text-sm">
              Dimension unit
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={dimensionsUnit} onChange={(e) => setDimensionsUnit(e.target.value)} />
            </label>
            <label className="text-sm">
              Milestone amount
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={milestoneAmount} onChange={(e) => setMilestoneAmount(e.target.value)} />
            </label>
          </div>
          <button type="button" disabled={busy} className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50" onClick={() => void onSavePlan()}>
            Record plan overlay
          </button>
        </div>
      ) : null}

      {tab === "CLAIM" ? (
        <div className="space-y-4">
          <p className="text-sm text-[var(--muted)]">
            Claims are statements being evaluated, not automatically true facts.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              Claimed progress %
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={progress} onChange={(e) => setProgress(e.target.value)} />
            </label>
            <label className="text-sm">
              Claimed expenditure
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={expenditure} onChange={(e) => setExpenditure(e.target.value)} />
            </label>
            <label className="text-sm">
              Completion state
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={completion} onChange={(e) => setCompletion(e.target.value)} />
            </label>
            <label className="text-sm">
              Claimed quantity
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
            </label>
            <label className="text-sm">
              Quantity unit
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={quantityUnit} onChange={(e) => setQuantityUnit(e.target.value)} />
            </label>
          </div>
          <button type="button" disabled={busy} className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50" onClick={() => void onSaveClaim()}>
            Record claim
          </button>
          <ul className="space-y-2 text-sm">
            {claims.map((item) => (
              <li key={item.claim_id ?? item.claim_date} className="border border-[var(--line)] p-3">
                Progress {item.claimed_progress_percent ?? "unavailable"} · expenditure {item.claimed_expenditure ?? "unavailable"} · quantity {item.claimed_quantity ?? "unavailable"} · {item.data_mode}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {tab === "EVIDENCE" ? (
        <div className="space-y-4">
          <p className="text-sm text-[var(--muted)]">
            Attach a PDF, image, blueprint, BOQ, or supporting document. Image forensics
            findings appear below as supporting evidence and do not mark a claim false.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              Document type
              <select className="mt-1 w-full border border-[var(--line)] p-2" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                <option value="pdf">PDF / document</option>
                <option value="blueprint">Blueprint</option>
                <option value="boq">BOQ</option>
                <option value="image">Image</option>
                <option value="supporting_document">Supporting document</option>
                <option value="inspection">Inspection</option>
                <option value="citizen">Citizen evidence</option>
              </select>
            </label>
            <label className="text-sm">
              Filename
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={filename} onChange={(e) => setFilename(e.target.value)} />
            </label>
            <label className="text-sm">
              Observed quantity
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={observedQuantity} onChange={(e) => setObservedQuantity(e.target.value)} />
            </label>
            <label className="text-sm">
              Observed expenditure
              <input className="mt-1 w-full border border-[var(--line)] p-2" value={observedExpenditure} onChange={(e) => setObservedExpenditure(e.target.value)} />
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={busy} className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50" onClick={() => void onAttach()}>
              Attach evidence
            </button>
            <button type="button" disabled={busy} className="border border-[var(--navy)] bg-[var(--navy)] px-3 py-1.5 text-sm text-white disabled:opacity-50" onClick={() => void onVerify()}>
              Run verification
            </button>
          </div>
          <ul className="space-y-2 text-sm">
            {attachments.map((item) => (
              <li key={`${item.document_id}-${item.photo_id}-${item.evidence_id}`} className="border border-[var(--line)] p-3">
                {item.evidence_kind} · {item.filename ?? "filename unavailable"} · {item.data_mode}
                {item.evidence_id ? ` · ${item.evidence_id}` : ""}
              </li>
            ))}
          </ul>
          {forensics.map((item) => (
            <ImageForensicsPceBlock key={`pce-forensic-${item.image_id}`} data={item} />
          ))}
          {satellite?.overall_result ? <SatellitePceBlock data={satellite} /> : null}
        </div>
      ) : null}

      {tab === "RESULT" ? (
        result ? (
          <div className="space-y-4">
            <VerificationResultBlock result={result} />
            {geo?.overall_result ? <GeospatialPceBlock data={geo} /> : null}
            {satellite?.overall_result ? <SatellitePceBlock data={satellite} /> : null}
            {forensics.map((item) => (
              <ImageForensicsPceBlock key={`result-forensic-${item.image_id}`} data={item} />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--muted)]">Run verification to see CONSISTENT, MISMATCH, or INCONCLUSIVE.</p>
            <button type="button" disabled={busy} className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50" onClick={() => void onVerify()}>
              Run verification
            </button>
          </div>
        )
      ) : null}
    </section>
  );
}

export type { ConsistencyResult };
