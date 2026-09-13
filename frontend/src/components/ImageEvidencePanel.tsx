"use client";

import { useCallback, useEffect, useState } from "react";

import {
  analyzeProjectImage,
  attachImageToEvidence,
  fetchProjectImages,
  uploadProjectImage,
} from "@/lib/api";
import type { DataMode, ImageSummary, ProjectImage } from "@/lib/types";

function modeLabel(mode: string | null | undefined) {
  if (mode === "SYNTHETIC" || mode === "HYBRID") {
    return mode;
  }
  return "REAL";
}

function confidencePct(value: number | null | undefined) {
  if (value == null) {
    return "unavailable";
  }
  return `${Math.round(Number(value) * 100)}%`;
}

export function ImageEvidencePanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [items, setItems] = useState<ProjectImage[]>([]);
  const [summary, setSummary] = useState<ImageSummary | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await fetchProjectImages(projectId, mode);
      setItems(body.items);
      setSummary(body.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Images could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onUpload = async () => {
    if (!file) {
      setError("Choose a JPEG, PNG, or WebP file first.");
      return;
    }
    setBusy(true);
    setError(null);
    setStatus("Uploading");
    try {
      await uploadProjectImage(projectId, file, mode);
      setStatus("Uploaded");
      setFile(null);
      await load();
    } catch (err) {
      setStatus("Upload failed");
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const onAnalyze = async (imageId: number) => {
    setBusy(true);
    setError(null);
    setStatus("Analyzing");
    try {
      await analyzeProjectImage(imageId);
      setStatus("Analyzed");
      await load();
    } catch (err) {
      setStatus("Analysis failed");
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setBusy(false);
    }
  };

  const onAttach = async (imageId: number) => {
    setBusy(true);
    setError(null);
    try {
      await attachImageToEvidence(imageId);
      setStatus("Attached to evidence");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evidence attach failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="text-xl font-semibold text-[var(--navy)]">Image Evidence</h2>
        <p className="mt-2 text-xs font-semibold tracking-[0.14em] text-[var(--signal)]">UPLOAD IMAGE</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Upload a progress photograph as supporting evidence. Exact duplicate and potential reuse are
          technical signals for review. They are not a legal finding. An image does not prove physical
          completion.
        </p>
      </div>
      {summary ? (
        <dl className="grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
          <div>
            Images submitted: <span className="font-medium">{summary.images_submitted}</span>
          </div>
          <div>
            Exact duplicate: <span className="font-medium">{summary.exact_duplicates}</span>
          </div>
          <div>
            Potential reuse: <span className="font-medium">{summary.potential_reuse}</span>
          </div>
          <div>
            GPS available: <span className="font-medium">{summary.gps_available}</span>
          </div>
          <div>
            GPS unavailable: <span className="font-medium">{summary.gps_unavailable}</span>
          </div>
          <div>
            Image-quality warnings: <span className="font-medium">{summary.quality_warnings}</span>
          </div>
          <div>
            Metadata available: <span className="font-medium">{summary.metadata_available}</span>
          </div>
          <div>
            Evidence confidence:{" "}
            <span className="font-medium">{confidencePct(summary.evidence_confidence)}</span>
          </div>
          <div>
            Advanced authenticity analysis:{" "}
            <span className="font-medium">{summary.advanced_authenticity_analysis}</span>
          </div>
        </dl>
      ) : null}
      <p className="text-sm">
        Upload status: <span className="font-medium">{status}</span>
      </p>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      <label className="text-sm">
        File (JPEG, PNG, WebP)
        <input
          className="mt-1 w-full border border-[var(--line)] p-2"
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <button
        type="button"
        disabled={busy}
        className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
        onClick={() => void onUpload()}
      >
        Upload image
      </button>
      <ul className="space-y-4">
        {items.map((item) => (
          <li key={item.image_id} className="space-y-3 border border-[var(--line)] p-4">
            <div className="flex flex-wrap items-start gap-4">
              {item.thumbnail_data_url ? (
                // Thumbnail is a JPEG data URL generated by the API; original filesystem path is not exposed.
                <img
                  src={item.thumbnail_data_url}
                  alt={item.filename ?? "Uploaded image thumbnail"}
                  className="h-24 w-24 border border-[var(--line)] object-cover"
                />
              ) : (
                <div className="flex h-24 w-24 items-center justify-center border border-[var(--line)] text-xs text-[var(--muted)]">
                  No thumbnail
                </div>
              )}
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium text-[var(--navy)]">{item.filename}</span>
                  {item.data_mode === "SYNTHETIC" || item.data_mode === "HYBRID" ? (
                    <span className="border border-[var(--saffron)] px-1.5 py-0.5 text-[10px] uppercase text-[var(--saffron)]">
                      {modeLabel(item.data_mode)} · SYNTHETIC
                    </span>
                  ) : (
                    <span className="border border-[var(--navy)] px-1.5 py-0.5 text-[10px] uppercase text-[var(--navy)]">
                      REAL
                    </span>
                  )}
                  <span className="text-xs text-[var(--muted)]">{item.integrity_status}</span>
                </div>
                <p className="text-xs text-[var(--muted)]">
                  {item.mime_type} · {item.file_size ?? "size unavailable"} bytes
                </p>
                <p className="break-all text-xs text-[var(--muted)]">
                  SHA-256 {item.content_sha256 ?? "unavailable"}
                </p>
                <p className="text-xs text-[var(--muted)]">
                  aHash {item.ahash ?? "unavailable"} · dHash {item.dhash ?? "unavailable"} · pHash{" "}
                  {item.phash ?? "unavailable"}
                </p>
              </div>
            </div>
            <div className="grid gap-2 text-sm lg:grid-cols-2">
              <p>
                Duplicate / reuse:{" "}
                {item.exact_duplicate
                  ? "EXACT_DUPLICATE"
                  : item.potential_reuse
                    ? "POTENTIAL_IMAGE_REUSE"
                    : "none detected"}
              </p>
              <p>Evidence confidence: {confidencePct(item.evidence_confidence)}</p>
              <p>
                GPS:{" "}
                {item.gps_available
                  ? `${item.latitude}, ${item.longitude}`
                  : item.gps_message ?? "GPS metadata unavailable."}
              </p>
              <p>Capture timestamp: {item.capture_timestamp ?? "METADATA_UNAVAILABLE"}</p>
              <p>Metadata: {item.metadata_status}</p>
              <p>
                Advanced authenticity: {item.authenticity.result} ({item.authenticity.capability})
              </p>
            </div>
            {(item.quality.warnings as string[] | undefined)?.length ? (
              <ul className="text-sm text-[var(--muted)]">
                {(item.quality.warnings as string[]).map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
            {item.reuse_matches.map((match) => (
              <p key={`${match.matched_image_id}-${match.hash_name}`} className="text-sm">
                {match.explanation} Confidence {confidencePct(match.confidence)}.
              </p>
            ))}
            {item.exact_matches.map((match) => (
              <p key={`${match.matched_image_id}-sha`} className="text-sm">
                {match.explanation} Confidence {confidencePct(match.confidence)}.
              </p>
            ))}
            <p className="text-xs text-[var(--muted)]">
              Metadata source: reported metadata from uploaded file. EXIF can be missing or edited.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => void onAnalyze(item.image_id)}
              >
                Analyze
              </button>
              <button
                type="button"
                disabled={busy}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => void onAttach(item.image_id)}
              >
                Attach to Evidence
              </button>
            </div>
            <ul className="text-xs text-[var(--muted)]">
              {(item.limitations ?? []).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
