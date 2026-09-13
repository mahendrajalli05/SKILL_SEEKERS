"use client";

import { useId, useState, type ReactNode } from "react";

export function LazyDisclosure({
  title,
  summary,
  children,
  defaultOpen = false,
}: {
  id?: string;
  title: string;
  summary: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const panelId = useId();
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="border border-[var(--line)] bg-[var(--surface)]">
      <h2>
        <button
          type="button"
          className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="font-semibold text-[var(--navy)]">{title}</span>
          <span className="text-xs uppercase tracking-wide text-[var(--muted)]">
            {open ? "Hide" : "Show"}
          </span>
        </button>
      </h2>
      {open ? (
        <div id={panelId} className="border-t border-[var(--line)] p-5">
          {children}
        </div>
      ) : (
        <p className="px-5 pb-4 text-sm text-[var(--muted)]">{summary}</p>
      )}
    </section>
  );
}
