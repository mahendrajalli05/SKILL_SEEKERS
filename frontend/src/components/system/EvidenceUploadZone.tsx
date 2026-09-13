"use client";

import { useRef, useState } from "react";

export function EvidenceUploadZone({
  accept = "image/jpeg,image/png,image/webp",
  label = "UPLOAD PROJECT PHOTO",
  helper = "JPG / PNG / WEBP",
  file,
  onFile,
}: {
  accept?: string;
  label?: string;
  helper?: string;
  file: File | null;
  onFile: (file: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const assign = (next: File | null) => {
    onFile(next);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(next && next.type.startsWith("image/") ? URL.createObjectURL(next) : null);
  };

  return (
    <div className="space-y-3">
      <button
        type="button"
        className="flex min-h-[12rem] w-full flex-col items-center justify-center border-2 border-dashed border-[var(--signal)] bg-[var(--signal-soft)] px-6 py-8 text-center"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          assign(event.dataTransfer.files?.[0] ?? null);
        }}
      >
        <p className="text-xs font-semibold tracking-[0.16em] text-[var(--signal)]">{label}</p>
        <p className="mt-3 text-lg font-semibold text-[var(--navy)]">Choose Photo</p>
        <p className="mt-1 text-sm text-[var(--muted)]">{helper}</p>
        {file ? <p className="mt-3 text-sm">{file.name}</p> : null}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(event) => assign(event.target.files?.[0] ?? null)}
      />
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="Selected project photo preview" className="max-h-64 w-full object-contain" />
      ) : null}
    </div>
  );
}
