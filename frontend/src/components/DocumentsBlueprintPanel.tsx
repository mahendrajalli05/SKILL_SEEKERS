"use client";

import { useCallback, useEffect, useState } from "react";

import {
  attachDocumentToEvidence,
  attachDocumentToPlan,
  extractDocument,
  fetchProjectDocuments,
  uploadProjectDocument,
} from "@/lib/api";
import type { DataMode, ExtractedFieldRead, PlanSourceConflict, ProjectDocument } from "@/lib/types";

const DOCUMENT_TYPES = [
  "BLUEPRINT",
  "BOQ_ESTIMATE",
  "PROJECT_DOCUMENT",
  "PROGRESS_REPORT",
  "COMPLETION_DOCUMENT",
  "OTHER",
] as const;

function modeLabel(mode: string | null | undefined) {
  if (mode === "SYNTHETIC" || mode === "HYBRID") {
    return mode;
  }
  return "REAL";
}

function FieldCard({ field }: { field: ExtractedFieldRead }) {
  const confidence =
    field.confidence == null ? null : `${Math.round(Number(field.confidence) * 100)}%`;
  return (
    <li className="border border-[var(--line)] p-3 text-sm">
      <p className="font-medium text-[var(--navy)]">{field.name.replaceAll("_", " ")}</p>
      {field.available ? (
        <p>
          {String(field.value)}
          {field.unit ? ` ${field.unit}` : ""}
        </p>
      ) : (
        <p className="text-[var(--muted)]">INCONCLUSIVE — {field.unavailable_reason}</p>
      )}
      <p className="mt-1 text-xs text-[var(--muted)]">
        EXTRACTION CONFIDENCE: {confidence ?? "unavailable"}
        {field.source_location ? ` · ${field.source_location}` : ""}
        {field.extraction_method ? ` · ${field.extraction_method}` : ""}
      </p>
    </li>
  );
}

export function DocumentsBlueprintPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [items, setItems] = useState<ProjectDocument[]>([]);
  const [conflicts, setConflicts] = useState<PlanSourceConflict[]>([]);
  const [documentType, setDocumentType] = useState<(typeof DOCUMENT_TYPES)[number]>("BLUEPRINT");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await fetchProjectDocuments(projectId, mode);
      setItems(body.items);
      setConflicts(body.conflicts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Documents could not be loaded.");
    }
  }, [projectId, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  const onUpload = async () => {
    if (!file) {
      setError("Choose a PDF, PNG, or JPEG file first.");
      return;
    }
    setBusy(true);
    setError(null);
    setStatus("Uploading");
    try {
      await uploadProjectDocument(projectId, file, documentType, mode);
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

  const onExtract = async (documentId: number) => {
    setBusy(true);
    setError(null);
    setStatus("Extracting");
    try {
      await extractDocument(documentId);
      setStatus("Extracted");
      await load();
    } catch (err) {
      setStatus("Extraction failed");
      setError(err instanceof Error ? err.message : "Extraction failed.");
    } finally {
      setBusy(false);
    }
  };

  const onAttachPlan = async (documentId: number) => {
    setBusy(true);
    setError(null);
    try {
      const result = await attachDocumentToPlan(documentId);
      if (result.conflicts.length) {
        setStatus("PLAN DATA CONFLICT");
      } else {
        setStatus("Attached to plan");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan attach failed.");
    } finally {
      setBusy(false);
    }
  };

  const onAttachEvidence = async (documentId: number) => {
    setBusy(true);
    setError(null);
    try {
      await attachDocumentToEvidence(documentId);
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
        <h2 className="text-xl font-semibold text-[var(--navy)]">Documents / Blueprint</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Upload project documents, extract labelled fields, and attach them to Plan or Evidence.
          Authenticity is not verified. This is not a legal finding.
        </p>
      </div>
      <p className="text-sm">
        Upload status: <span className="font-medium">{status}</span>
      </p>
      {error ? <p className="text-sm text-[var(--saffron)]">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          Document type
          <select
            className="mt-1 w-full border border-[var(--line)] p-2"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as (typeof DOCUMENT_TYPES)[number])}
          >
            {DOCUMENT_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          File (PDF, PNG, JPEG)
          <input
            className="mt-1 w-full border border-[var(--line)] p-2"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>
      <button
        type="button"
        disabled={busy}
        className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
        onClick={() => void onUpload()}
      >
        Upload document
      </button>
      {conflicts.length > 0 ? (
        <div className="border border-[var(--saffron)] p-3">
          <h3 className="text-sm font-semibold text-[var(--navy)]">PLAN DATA CONFLICT</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {conflicts.map((item) => (
              <li key={`${item.field}-${item.result}`}>
                {item.field}: {item.explanation}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <ul className="space-y-4">
        {items.map((item) => (
          <li key={item.document_id} className="space-y-3 border border-[var(--line)] p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium text-[var(--navy)]">{item.filename}</span>
              <span className="border border-[var(--line)] px-1.5 py-0.5 text-[10px] uppercase">
                {item.document_type}
              </span>
              {item.data_mode === "SYNTHETIC" || item.data_mode === "HYBRID" ? (
                <span className="border border-[var(--saffron)] px-1.5 py-0.5 text-[10px] uppercase text-[var(--saffron)]">
                  {modeLabel(item.data_mode)} · SYNTHETIC
                </span>
              ) : (
                <span className="border border-[var(--navy)] px-1.5 py-0.5 text-[10px] uppercase text-[var(--navy)]">
                  REAL
                </span>
              )}
              <span className="text-xs text-[var(--muted)]">{item.extraction_status}</span>
              {item.integrity_status ? (
                <span className="text-xs text-[var(--muted)]">{item.integrity_status}</span>
              ) : null}
            </div>
            <p className="text-xs text-[var(--muted)]">
              {item.mime_type} · {item.file_size ?? "size unavailable"} bytes · hash {item.content_sha256 ?? "unavailable"}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => void onExtract(item.document_id)}
              >
                Extract
              </button>
              <button
                type="button"
                disabled={busy || item.extraction_status === "NOT_RUN"}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => void onAttachPlan(item.document_id)}
              >
                Attach to Plan
              </button>
              <button
                type="button"
                disabled={busy || item.extraction_status === "NOT_RUN"}
                className="border border-[var(--navy)] px-3 py-1.5 text-sm text-[var(--navy)] disabled:opacity-50"
                onClick={() => void onAttachEvidence(item.document_id)}
              >
                Attach to Evidence
              </button>
            </div>
            {item.extraction ? (
              <div>
                <p className="text-sm">
                  Extraction: {item.extraction.status} · method {item.extraction.extraction_method}
                </p>
                <ul className="mt-2 grid gap-2 lg:grid-cols-2">
                  {(item.extraction.fields ?? []).map((field) => (
                    <FieldCard key={`${item.document_id}-${field.name}`} field={field} />
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-[var(--muted)]">Extraction has not been run for this file.</p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}