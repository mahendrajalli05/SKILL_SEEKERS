"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchImageForensics, fetchProjectImages, runImageForensics } from "@/lib/api";
import type { DataMode, ImageForensicsResponse, ProjectImage } from "@/lib/types";

function displayResult(value: string) {
  if (value === "POTENTIAL_MANIPULATION") return "Potential signal";
  if (value === "POTENTIAL_AI_GENERATION") return "Potential signal";
  if (value === "AI_GENERATION_ANALYSIS_UNAVAILABLE") return "Inconclusive";
  if (value === "METADATA_ANOMALY") return "Potential metadata anomaly";
  if (value === "TIMESTAMP_AVAILABLE") return "Timestamp available";
  if (value === "EXIF_UNAVAILABLE" || value === "INCONCLUSIVE") return "Inconclusive";
  if (value === "EXACT_DUPLICATE") return "Exact duplicate";
  if (value === "POTENTIAL_IMAGE_REUSE") return "Potential reuse";
  if (value === "UNIQUE") return "No match";
  if (value === "NO_STRONG_FORENSIC_SIGNAL") return "No strong signal";
  if (value === "REVIEW_REQUIRED") return "REVIEW REQUIRED";
  if (value === "QUALITY_WARNING") return "Quality warning";
  return value.replaceAll("_", " ");
}

function metadataDisplay(signal: ImageForensicsResponse["metadata_signal"]) {
  const display = typeof signal.details.display === "string" ? signal.details.display : signal.result;
  if (display === "TIMESTAMP_AVAILABLE") return "Timestamp available";
  if (display === "EXIF_UNAVAILABLE") return "EXIF unavailable";
  if (display === "METADATA_ANOMALY") return "Potential metadata anomaly";
  if (display === "TIMESTAMP_UNAVAILABLE") return "Timestamp unavailable";
  return displayResult(signal.result);
}

function resultClass(result: string) {
  if (result === "REVIEW_REQUIRED" || result === "Review required.") {
    return "border-[var(--saffron)] bg-[#f8efe6]";
  }
  return "border-[var(--line)] bg-white";
}

export function ImageForensicsPceBlock({ data }: { data: ImageForensicsResponse | null }) {
  if (!data?.plan_claim_evidence) {
    return null;
  }
  const pce = data.plan_claim_evidence;
  return (
    <section className={`space-y-2 border p-4 ${resultClass(data.overall_assessment)}`}>
      <h4 className="text-sm font-semibold text-[var(--navy)]">Image forensics (Plan → Claim → Evidence)</h4>
      <p className="text-sm">CLAIM: {pce.claim ?? "Photo shows completed work."}</p>
      <p className="text-sm">FORENSIC: {pce.forensic}</p>
      <p className="text-sm font-medium">Result: {pce.result}</p>
      <p className="text-xs text-[var(--muted)]">{pce.note}</p>
    </section>
  );
}

export function ImageForensicsPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [images, setImages] = useState<ProjectImage[]>([]);
  const [items, setItems] = useState<ImageForensicsResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const listed = await fetchProjectImages(projectId, mode);
      setImages(listed.items);
      const next: ImageForensicsResponse[] = [];
      for (const image of listed.items) {
        try {
          next.push(await fetchImageForensics(image.image_id, mode));
        } catch {
          /* per-image forensics remain optional until the officer runs them */
        }
      }
      setItems(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image forensics could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onRun = async (imageId: number) => {
    setBusy(true);
    setError(null);
    try {
      const body = await runImageForensics(imageId, mode);
      setItems((current) => {
        const others = current.filter((item) => item.image_id !== imageId);
        return [...others, body];
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Forensic analysis could not be run.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="text-xl font-semibold text-[var(--navy)]">Image Forensics</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Decision-support signals for submitted photographs. This is not a validated authenticity
          decision and does not mark a claim false.
        </p>
      </div>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      {images.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">No images are available in this data mode.</p>
      ) : null}
      {items.map((item) => (
        <article key={item.image_id} className={`space-y-3 border p-4 ${resultClass(item.overall_assessment)}`}>
          <div className="flex flex-wrap items-start gap-4">
            {item.thumbnail_data_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={item.thumbnail_data_url} alt="" className="h-24 w-24 border border-[var(--line)] object-cover" />
            ) : (
              <div className="flex h-24 w-24 items-center justify-center border border-[var(--line)] text-xs text-[var(--muted)]">
                Image
              </div>
            )}
            <div className="space-y-1 text-sm">
              <p className="font-medium text-[var(--navy)]">{item.filename ?? `Image ${item.image_id}`}</p>
              <p>Integrity: {item.integrity.status}</p>
              <p>Metadata: {metadataDisplay(item.metadata_signal)}</p>
              <p>Reuse: {displayResult(item.reuse_signal.result)}</p>
              <p>Manipulation signal: {displayResult(item.manipulation_signal.result)}</p>
              <p>AI-generation signal: {displayResult(item.ai_generation_signal.result)}</p>
              <p>Confidence: {item.confidence_label}</p>
              <p className="font-medium">Overall forensic assessment: {displayResult(item.overall_assessment)}</p>
              <p className="text-xs text-[var(--muted)]">{item.prototype_assessment_label}</p>
              <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{item.data_mode}</p>
            </div>
          </div>
          <ImageForensicsPceBlock data={item} />
          <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--muted)]">
            {item.limitations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <button
            type="button"
            disabled={busy}
            className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
            onClick={() => void onRun(item.image_id)}
          >
            Run forensics
          </button>
        </article>
      ))}
      {images.map((image) =>
        items.some((item) => item.image_id === image.image_id) ? null : (
          <button
            key={`run-${image.image_id}`}
            type="button"
            disabled={busy}
            className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
            onClick={() => void onRun(image.image_id)}
          >
            Run forensics for {image.filename ?? image.image_id}
          </button>
        ),
      )}
    </section>
  );
}
