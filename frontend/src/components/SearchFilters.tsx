import { StyledSelect } from "@/components/ui/StyledSelect";
import { SELECT_STATE_FIRST } from "@/lib/display";
import type { ProjectSearchOptionsResponse } from "@/lib/types";

export function SearchFilters({
  stateFilter,
  constituency,
  category,
  status,
  q,
  schemeId,
  internalId,
  options,
  onStateChange,
  onConstituencyChange,
  onCategoryChange,
  onStatusChange,
  onQueryChange,
  onSchemeIdChange,
  onInternalIdChange,
  onClearQuery,
}: {
  stateFilter: string;
  constituency: string;
  category: string;
  status: string;
  q: string;
  schemeId?: string;
  internalId?: string;
  options: ProjectSearchOptionsResponse | null;
  onStateChange: (value: string) => void;
  onConstituencyChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSchemeIdChange?: (value: string) => void;
  onInternalIdChange?: (value: string) => void;
  onClearQuery?: () => void;
}) {
  const constituencyEnabled = Boolean(stateFilter) && Boolean(options?.constituency_enabled);
  return (
    <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
      <div className="text-sm">
        <label htmlFor="search-scheme" className="font-medium text-[var(--navy)]">
          Scheme ID
        </label>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Internal SARVSAKSHI identifier, not an official MPLADS work ID.
        </p>
        <input
          id="search-scheme"
          className="svk-input mt-1"
          value={schemeId ?? ""}
          onChange={(event) => onSchemeIdChange?.(event.target.value)}
          placeholder="e.g. SVK-AP-000139"
        />
      </div>
      <div className="text-sm">
        <label htmlFor="search-internal" className="font-medium text-[var(--navy)]">
          Internal Project ID
        </label>
        <p className="mt-1 text-xs text-[var(--muted)]">Stored SARVSAKSHI surrogate key.</p>
        <input
          id="search-internal"
          className="svk-input mt-1"
          value={internalId ?? ""}
          onChange={(event) => onInternalIdChange?.(event.target.value)}
          placeholder="Internal project ID"
        />
      </div>
      <div className="text-sm">
        <label htmlFor="search-q" className="font-medium text-[var(--navy)]">
          Work description / MP
        </label>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Partial match across work text and MP name. Also accepts Scheme ID.
        </p>
        <input
          id="search-q"
          className="svk-input mt-1"
          value={q}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Scheme ID, Internal Project ID, work description, or MP name"
          maxLength={200}
          autoComplete="off"
        />
      </div>
      <StyledSelect
        id="search-state"
        label="State"
        description="Choose state before constituency."
        value={stateFilter}
        onChange={onStateChange}
        placeholder="Select state"
        options={(options?.states ?? []).map((item) => ({ value: item, label: item }))}
      />
      <StyledSelect
        id="search-constituency"
        label="Constituency"
        description="Enabled after a state is selected."
        value={constituencyEnabled ? constituency : ""}
        onChange={onConstituencyChange}
        disabled={!constituencyEnabled}
        placeholder={constituencyEnabled ? "All geographic constituencies" : SELECT_STATE_FIRST}
        options={(options?.constituencies ?? []).map((item) => ({ value: item, label: item }))}
      />
      <StyledSelect
        id="search-category"
        label="Category"
        description="Observed MPLADS category values only."
        value={category}
        onChange={onCategoryChange}
        placeholder="All observed categories"
        options={(options?.categories ?? []).map((item) => ({ value: item, label: item }))}
      />
      <StyledSelect
        id="search-status"
        label="Status"
        description="Observed source status, not a legal conclusion."
        value={status}
        onChange={onStatusChange}
        placeholder="All observed statuses"
        options={(options?.statuses ?? []).map((item) => ({ value: item, label: item }))}
      />
      <div className="flex items-end gap-2 md:col-span-2 lg:col-span-3">
        <button type="submit" className="svk-btn svk-btn-primary">
          Search
        </button>
        <button
          type="button"
          className="svk-btn"
          onClick={() => {
            onQueryChange("");
            onSchemeIdChange?.("");
            onInternalIdChange?.("");
            onClearQuery?.();
          }}
        >
          Clear search
        </button>
      </div>
    </div>
  );
}
