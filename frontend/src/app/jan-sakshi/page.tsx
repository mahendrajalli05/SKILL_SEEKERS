"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { EvidenceUploadZone } from "@/components/system/EvidenceUploadZone";
import { PageHeader } from "@/components/system/PageHeader";
import { WorkflowStepper } from "@/components/system/WorkflowStepper";
import { StyledSelect } from "@/components/ui/StyledSelect";
import { fetchProjectOptions, fetchProjects, submitCitizenReport } from "@/lib/api";
import { FEATURE_EXPLANATIONS, GEO_PROTOTYPE_RULE } from "@/lib/explanations";
import { displayText, formatAllocation } from "@/lib/display";
import type { CitizenReport, ProjectSearchItem, ProjectSearchOptionsResponse } from "@/lib/types";

const ISSUES = [
  { value: "work_quality", label: "Work quality" },
  { value: "incomplete_work", label: "Incomplete work" },
  { value: "delayed_work", label: "Delayed work" },
  { value: "location_concern", label: "Location concern" },
  { value: "safety", label: "Safety" },
  { value: "other", label: "Other" },
];

export default function JanSakshiPage() {
  const [finder, setFinder] = useState<"scheme" | "browse">("scheme");
  const [query, setQuery] = useState("");
  const [constituency, setConstituency] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [options, setOptions] = useState<ProjectSearchOptionsResponse | null>(null);
  const [matches, setMatches] = useState<ProjectSearchItem[]>([]);
  const [project, setProject] = useState<ProjectSearchItem | null>(null);
  const [rating, setRating] = useState(3);
  const [issue, setIssue] = useState("other");
  const [observation, setObservation] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [locationNote, setLocationNote] = useState("Location not captured yet.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CitizenReport | null>(null);

  const canSubmit = useMemo(
    () => Boolean(project) && (observation.trim().length > 0 || file || rating),
    [project, observation, file, rating],
  );

  useEffect(() => {
    fetchProjectOptions("Andhra Pradesh")
      .then(setOptions)
      .catch(() => setOptions(null));
  }, []);

  const onSearch = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const body = await fetchProjects({
        q: finder === "scheme" ? query : undefined,
        constituency: finder === "browse" ? constituency : undefined,
        category: finder === "browse" ? category : undefined,
        status: finder === "browse" ? status : undefined,
        state: "Andhra Pradesh",
        apply_pilot_scope: true,
        page: 1,
        page_size: 8,
        mode: "hybrid",
      });
      setMatches(body.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project search failed.");
    }
  };

  const captureLocation = () => {
    if (!navigator.geolocation) {
      setLocationNote("Browser geolocation is unavailable.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setLocationNote("Location captured for verification only. It is not published.");
      },
      () => {
        setLocationNote("Location unavailable. The submission can still be sent and may be INCONCLUSIVE.");
        setLatitude(null);
        setLongitude(null);
      },
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      const body = await submitCitizenReport(project.id, {
        satisfaction_rating: rating,
        observation_text: observation,
        issue_category: issue,
        latitude,
        longitude,
        capture_timestamp: new Date().toISOString(),
        data_mode: "HYBRID",
        file,
      });
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission was not accepted.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader kicker="Citizen evidence" title="JAN-SAKSHI" explanation={FEATURE_EXPLANATIONS.citizen}>
        <p className="mt-2 text-lg text-[var(--navy)]">Help us understand what is happening on the ground.</p>
      </PageHeader>

      <WorkflowStepper steps={["FIND PROJECT", "SUBMIT EVIDENCE", "VERIFY LOCATION", "SUBMIT"]} current={result ? 3 : project ? 1 : 0} />

      <form onSubmit={onSearch} className="svk-panel space-y-4 p-6">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">01 FIND PROJECT</h2>
        <p className="text-sm text-[var(--muted)]">You do not need to know the Scheme ID.</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={`svk-btn ${finder === "scheme" ? "svk-btn-primary" : ""}`}
            onClick={() => setFinder("scheme")}
          >
            I know the Scheme ID
          </button>
          <button
            type="button"
            className={`svk-btn ${finder === "browse" ? "svk-btn-primary" : ""}`}
            onClick={() => setFinder("browse")}
          >
            Find my project
          </button>
        </div>
        {finder === "scheme" ? (
          <label className="block text-sm">
            <span className="font-medium text-[var(--navy)]">Scheme ID or work name</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Scheme ID, work, or MP name"
              className="svk-input mt-2"
            />
          </label>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            <StyledSelect
              label="Constituency"
              value={constituency}
              onChange={setConstituency}
              placeholder="Any constituency"
              options={(options?.constituencies ?? []).map((item) => ({ value: item, label: item }))}
            />
            <StyledSelect
              label="Project type"
              value={category}
              onChange={setCategory}
              placeholder="Any type"
              options={(options?.categories ?? []).map((item) => ({ value: item, label: item }))}
            />
            <StyledSelect
              label="Project status"
              value={status}
              onChange={setStatus}
              placeholder="Any status"
              options={(options?.statuses ?? []).map((item) => ({ value: item, label: item }))}
            />
          </div>
        )}
        <p className="text-xs text-[var(--muted)]">{GEO_PROTOTYPE_RULE}</p>
        <button type="submit" className="svk-btn svk-btn-primary">
          Search
        </button>
        <ul className="mt-3 space-y-2">
          {matches.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => setProject(item)}
                className="w-full border border-[var(--line)] bg-white p-3 text-left hover:border-[var(--signal)]"
              >
                <p className="svk-mono text-sm font-medium">{displayText(item.scheme_id)}</p>
                <p className="text-sm">{displayText(item.work_description)}</p>
                <p className="text-xs text-[var(--muted)]">
                  {displayText(item.constituency)} · {displayText(item.status)} · {formatAllocation(item.allocation_amount)}
                </p>
              </button>
            </li>
          ))}
        </ul>
        {project ? (
          <section className="svk-card p-4" data-tone="success">
            <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--success)]">SELECTED PROJECT</p>
            <p className="svk-mono mt-2 text-sm font-semibold">{displayText(project.scheme_id)}</p>
            <p className="text-sm">{displayText(project.work_description)}</p>
            <p className="text-xs text-[var(--muted)]">
              {displayText(project.constituency)} · {displayText(project.status)} · {formatAllocation(project.allocation_amount)}
            </p>
          </section>
        ) : null}
      </form>

      <form onSubmit={onSubmit} className="svk-panel space-y-6 p-6">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">02 SUBMIT EVIDENCE</h2>
        <EvidenceUploadZone file={file} onFile={setFile} />
        <section>
          <h3 className="svk-display text-lg font-semibold text-[var(--navy)]">03 VERIFY LOCATION</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Location is used for verification only. Raw citizen GPS is not published.
          </p>
          <button type="button" onClick={captureLocation} className="svk-btn mt-3">
            Use Current Location
          </button>
          <p className="mt-2 text-xs text-[var(--muted)]">{locationNote}</p>
        </section>
        <section>
          <h3 className="font-semibold text-[var(--navy)]">SATISFACTION</h3>
          <div className="mt-2 flex gap-2" role="radiogroup" aria-label="Satisfaction (1–5 stars)">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                className={`h-10 w-10 border ${rating >= value ? "bg-[var(--saffron-soft)] border-[var(--saffron)]" : "border-[var(--line)] bg-white"}`}
                onClick={() => setRating(value)}
                aria-checked={rating === value}
                role="radio"
              >
                <span className="sr-only">{value} star{value === 1 ? "" : "s"}</span>
                <span aria-hidden>★</span>
              </button>
            ))}
          </div>
        </section>
        <StyledSelect
          label="Issue category"
          value={issue}
          onChange={setIssue}
          options={ISSUES}
          description="Choose the closest description of what you observed."
        />
        <label className="block text-sm">
          Observation
          <textarea
            value={observation}
            onChange={(event) => setObservation(event.target.value)}
            className="svk-textarea mt-1"
            rows={5}
          />
        </label>
        <h3 className="svk-display text-lg font-semibold text-[var(--navy)]">04 SUBMIT</h3>
        <button type="submit" disabled={!canSubmit || busy} className="svk-btn svk-btn-primary disabled:opacity-50">
          {busy ? "Submitting…" : "Submit Field Evidence"}
        </button>
      </form>

      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      {result ? (
        <section className="svk-card border-[var(--success)] p-8 text-center" data-tone="success">
          <p className="text-4xl text-[var(--success)]" aria-hidden>✓</p>
          <h2 className="svk-display mt-2 text-xl font-semibold text-[var(--navy)]">Evidence submitted successfully</h2>
          <p className="mt-2 text-sm">
            Recorded against: <span className="svk-mono">{result.scheme_id}</span>
          </p>
          <p className="mt-2 text-sm">
            {result.submission_status} / {result.verification_result}
          </p>
          <p className="mt-2 text-sm">{result.reasons.join(" ")}</p>
          <p className="mt-2 text-xs text-[var(--muted)]">{result.governance_note}</p>
        </section>
      ) : null}
    </div>
  );
}
