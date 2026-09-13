"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { PageState } from "@/components/ui/PageState";
import { fetchProjects } from "@/lib/api";
import { displayText, formatAllocation, parseDataMode } from "@/lib/display";
import type { DataMode, ProjectSearchItem } from "@/lib/types";

export function ProjectSelector({
  mode,
  selected,
  onSelect,
  heading = "Select a project",
  helper = "Search by Scheme ID, work description, MP, or constituency.",
}: {
  mode: DataMode;
  selected?: ProjectSearchItem | null;
  onSelect: (item: ProjectSearchItem) => void;
  heading?: string;
  helper?: string;
}) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ProjectSearchItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const engineMode = mode === "REAL" ? "real" : "hybrid";

  const onSearch = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = await fetchProjects({
        q: query,
        page: 1,
        page_size: 8,
        apply_pilot_scope: true,
        mode: engineMode,
      });
      setItems(body.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project search failed.");
    } finally {
      setBusy(false);
    }
  };

  const empty = useMemo(() => items.length === 0 && !busy, [items, busy]);

  return (
    <section className="svk-panel p-5">
      <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">{heading}</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">{helper}</p>
      <form onSubmit={onSearch} className="mt-4 flex flex-col gap-3 sm:flex-row">
        <label className="flex-1 text-sm">
          <span className="sr-only">Find a project</span>
          <input
            className="svk-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Scheme ID, work, MP, or constituency"
          />
        </label>
        <button type="submit" className="svk-btn svk-btn-primary" disabled={busy}>
          {busy ? "Searching…" : "Search"}
        </button>
      </form>
      {error ? <PageState kind="error" message={error} compact /> : null}
      {selected ? (
        <p className="mt-3 text-sm">
          Selected: <span className="svk-mono font-medium">{displayText(selected.scheme_id)}</span> ·{" "}
          {displayText(selected.work_description)}
        </p>
      ) : null}
      {empty && !error ? (
        <p className="mt-3 text-sm text-[var(--muted)]">No matching projects in this search yet.</p>
      ) : null}
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onSelect(item)}
              className="w-full border border-[var(--line)] bg-white p-3 text-left hover:border-[var(--signal)]"
            >
              <p className="svk-mono text-sm font-medium text-[var(--navy)]">{displayText(item.scheme_id)}</p>
              <p className="text-sm">{displayText(item.work_description)}</p>
              <p className="text-xs text-[var(--muted)]">
                {displayText(item.constituency)} · {formatAllocation(item.allocation_amount)}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function useSelectedProjectId(searchParams: URLSearchParams): number | null {
  const raw = Number(searchParams.get("project") ?? "");
  return Number.isFinite(raw) && raw > 0 ? raw : null;
}

export function parseHubMode(searchParams: URLSearchParams): DataMode {
  return parseDataMode(searchParams.get("mode"));
}
