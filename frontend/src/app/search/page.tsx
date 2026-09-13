"use client";

import Link from "next/link";
import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { SearchFilters } from "@/components/SearchFilters";
import { DataModeBanner } from "@/components/DataModeBanner";
import { PageHeader } from "@/components/system/PageHeader";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { fetchProjectOptions, fetchProjects, fetchScope } from "@/lib/api";
import {
  DEFAULT_PILOT_STATE,
  PILOT_LABEL,
  displayText,
  formatAllocation,
  lifecycleFromStatus,
  parseDataMode,
  withModePath,
} from "@/lib/display";
import { HighlightedText } from "@/lib/highlight";
import { buildSearchQueryString, parseSearchUrl } from "@/lib/searchUrl";
import type { ProjectSearchItem, ProjectSearchOptionsResponse } from "@/lib/types";

const PAGE_SIZE = 20;

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlKey = searchParams.toString();
  const urlState = useMemo(() => parseSearchUrl(searchParams), [searchParams, urlKey]);
  const mode = parseDataMode(urlState.mode);

  const [qDraft, setQDraft] = useState(urlState.q);
  const [q, setQ] = useState(urlState.q);
  const [schemeId, setSchemeId] = useState(urlState.scheme_id);
  const [internalId, setInternalId] = useState(urlState.internal_project_id);
  const [constituency, setConstituency] = useState(urlState.constituency);
  const [category, setCategory] = useState(urlState.category);
  const [status, setStatus] = useState(urlState.status);
  const [stateFilter, setStateFilter] = useState(urlState.state || DEFAULT_PILOT_STATE);
  const [page, setPage] = useState(urlState.page);
  const [total, setTotal] = useState(0);
  const [items, setItems] = useState<ProjectSearchItem[]>([]);
  const [note, setNote] = useState("");
  const [pilotLabel, setPilotLabel] = useState(PILOT_LABEL);
  const [options, setOptions] = useState<ProjectSearchOptionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const committedQuery = q.trim();
  const hasTextQuery = Boolean(committedQuery || schemeId.trim() || internalId.trim());

  const query = useMemo(
    () => ({
      q,
      scheme_id: schemeId.trim() || undefined,
      internal_project_id: internalId.trim() || undefined,
      constituency: stateFilter ? constituency : "",
      category,
      status,
      state: stateFilter,
      apply_pilot_scope: Boolean(stateFilter),
      mode: mode === "REAL" ? "real" : "hybrid",
      page,
      page_size: PAGE_SIZE,
    }),
    [q, schemeId, internalId, constituency, category, status, stateFilter, mode, page],
  );

  useEffect(() => {
    setQDraft(urlState.q);
    setQ(urlState.q);
    setSchemeId(urlState.scheme_id);
    setInternalId(urlState.internal_project_id);
    setConstituency(urlState.constituency);
    setCategory(urlState.category);
    setStatus(urlState.status);
    setStateFilter(urlState.state || DEFAULT_PILOT_STATE);
    setPage(urlState.page);
  }, [urlKey, urlState]);

  const replaceUrl = (next: {
    q?: string;
    state?: string;
    constituency?: string;
    category?: string;
    status?: string;
    page?: number;
    scheme_id?: string;
    internal_project_id?: string;
  }) => {
    const qs = buildSearchQueryString({
      q: next.q ?? q,
      state: next.state ?? stateFilter,
      constituency: next.constituency ?? constituency,
      category: next.category ?? category,
      status: next.status ?? status,
      page: next.page ?? page,
      mode: mode === "REAL" ? "real" : "hybrid",
      scheme_id: next.scheme_id ?? schemeId,
      internal_project_id: next.internal_project_id ?? internalId,
    });
    router.replace(qs ? `/search?${qs}` : "/search");
  };

  useEffect(() => {
    fetchScope()
      .then((body) => {
        setPilotLabel(body.pilot_label);
        setStateFilter((current) => current || body.default_state);
      })
      .catch(() => setPilotLabel(PILOT_LABEL));
  }, []);

  useEffect(() => {
    fetchProjectOptions(stateFilter || undefined)
      .then(setOptions)
      .catch(() => setOptions(null));
  }, [stateFilter]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchProjects(query)
      .then((body) => {
        if (cancelled) {
          return;
        }
        setItems(body.items);
        setTotal(body.total);
        setNote(body.note);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Search failed.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [query]);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    const nextQ = qDraft.trim();
    setQ(nextQ);
    setPage(1);
    replaceUrl({ q: nextQ, page: 1 });
  };

  const openProject = (id: number) => {
    router.push(withModePath(`/projects/${id}`, mode));
  };

  const onRowKey = (event: KeyboardEvent<HTMLTableRowElement>, id: number) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openProject(id);
    }
  };

  const emptyMessage = hasTextQuery
    ? "No matching projects found"
    : "No matching works in the current application scope.";

  return (
    <div className="space-y-5">
      <PageHeader kicker="Projects" title="PROJECTS" explanation={FEATURE_EXPLANATIONS.search}>
        <p className="mt-1 text-sm font-medium text-[var(--navy)]">{pilotLabel}</p>
      </PageHeader>

      <DataModeBanner mode={mode} />

      <form onSubmit={onSubmit} className="svk-panel p-5">
        <h2 className="text-sm font-semibold tracking-[0.12em] text-[var(--navy)]">SEARCH AND FILTERS</h2>
        <SearchFilters
          stateFilter={stateFilter}
          constituency={constituency}
          category={category}
          status={status}
          q={qDraft}
          schemeId={schemeId}
          internalId={internalId}
          options={options}
          onStateChange={(value) => {
            setStateFilter(value);
            setConstituency("");
            setPage(1);
            replaceUrl({ state: value, constituency: "", page: 1 });
          }}
          onConstituencyChange={(value) => {
            setConstituency(value);
            setPage(1);
            replaceUrl({ constituency: value, page: 1 });
          }}
          onCategoryChange={(value) => {
            setCategory(value);
            setPage(1);
            replaceUrl({ category: value, page: 1 });
          }}
          onStatusChange={(value) => {
            setStatus(value);
            setPage(1);
            replaceUrl({ status: value, page: 1 });
          }}
          onQueryChange={setQDraft}
          onSchemeIdChange={(value) => {
            setSchemeId(value);
          }}
          onInternalIdChange={(value) => {
            setInternalId(value);
          }}
          onClearQuery={() => {
            setQDraft("");
            setQ("");
            setSchemeId("");
            setInternalId("");
            setPage(1);
            replaceUrl({ q: "", scheme_id: "", internal_project_id: "", page: 1 });
          }}
        />
        <p className="mt-3 text-xs text-[var(--muted)]">{note}</p>
      </form>

      {error ? <PageState kind="error" message={error} /> : null}

      <div className="flex items-end justify-between gap-3">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">
          RESULTS — {loading ? "…" : total.toLocaleString("en-IN")} PROJECTS
        </h2>
      </div>

      <section className="svk-table-wrap" aria-busy={loading}>
        <table className="svk-table svk-table-stack">
          <caption className="sr-only">Project search results</caption>
          <thead>
            <tr>
              <th scope="col">Scheme ID</th>
              <th scope="col">Project</th>
              <th scope="col">Constituency</th>
              <th scope="col">Category</th>
              <th scope="col">Amount</th>
              <th scope="col">Lifecycle</th>
              <th scope="col">Status</th>
              <th scope="col">Signals</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-3 py-4 text-[var(--muted)]" colSpan={9}>
                  Loading search results…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-[var(--muted)]" colSpan={9}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr
                  key={item.id}
                  data-clickable="true"
                  tabIndex={0}
                  onClick={() => openProject(item.id)}
                  onKeyDown={(event) => onRowKey(event, item.id)}
                >
                  <td data-label="Scheme ID" className="svk-mono font-medium text-[var(--navy)]">
                    <HighlightedText text={displayText(item.scheme_id)} query={committedQuery} />
                  </td>
                  <td data-label="Project">
                    <Link
                      className="font-medium text-[var(--navy)] underline-offset-2 hover:underline"
                      href={withModePath(`/projects/${item.id}`, mode)}
                      onClick={(event) => event.stopPropagation()}
                    >
                      <HighlightedText text={displayText(item.work_description)} query={committedQuery} />
                    </Link>
                    <p className="text-xs text-[var(--muted)]">
                      <HighlightedText text={item.internal_project_id} query={committedQuery} />
                    </p>
                  </td>
                  <td data-label="Constituency">{displayText(item.constituency)}</td>
                  <td data-label="Category">{displayText(item.category)}</td>
                  <td data-label="Amount">{formatAllocation(item.allocation_amount)}</td>
                  <td data-label="Lifecycle">
                    <StatusBadge value={lifecycleFromStatus(item.status)} />
                  </td>
                  <td data-label="Status">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge value={item.status} />
                      <StatusBadge value={String(item.data_mode)} />
                    </div>
                  </td>
                  <td data-label="Signals">
                    <StatusBadge value={String(item.data_mode)} />
                  </td>
                  <td data-label="Action">
                    <div className="flex flex-wrap gap-2">
                      <Link
                        className="svk-btn"
                        href={withModePath(`/projects/${item.id}`, mode)}
                        onClick={(event) => event.stopPropagation()}
                      >
                        View Passport
                      </Link>
                      <Link
                        className="svk-btn svk-btn-primary"
                        href={withModePath(`/projects/${item.id}/investigate`, mode)}
                        onClick={(event) => event.stopPropagation()}
                      >
                        Investigate
                      </Link>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <p className="text-[var(--muted)]">
          {loading ? "Loading…" : `${total} works`} · page {page} of {pageCount} · {pilotLabel}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            className="svk-btn disabled:opacity-50"
            disabled={loading || page <= 1}
            onClick={() => {
              const next = Math.max(1, page - 1);
              setPage(next);
              replaceUrl({ page: next });
            }}
          >
            Previous
          </button>
          <button
            type="button"
            className="svk-btn disabled:opacity-50"
            disabled={loading || page >= pageCount}
            onClick={() => {
              const next = page + 1;
              setPage(next);
              replaceUrl({ page: next });
            }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
