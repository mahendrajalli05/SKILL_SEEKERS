import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SearchFilters } from "@/components/SearchFilters";
import type { ProjectSearchOptionsResponse } from "@/lib/types";

const options: ProjectSearchOptionsResponse = {
  states: ["Andhra Pradesh", "Maharashtra"],
  constituencies: ["ONGOLE", "ELURU"],
  excluded_non_geographic_constituencies: ["Sitting Rajya Sabha"],
  categories: ["Roads", "Education"],
  statuses: ["Ongoing", "Completed"],
  constituency_enabled: true,
  constituency_placeholder: null,
  selected_state: "Andhra Pradesh",
  pilot_label: "Current Pilot: Andhra Pradesh",
  note: "State first.",
};

describe("SearchFilters text search actions", () => {
  it("updates the draft query without requiring a page reload", async () => {
    const user = userEvent.setup();
    const onQueryChange = vi.fn();
    render(
      <form>
        <SearchFilters
          stateFilter="Andhra Pradesh"
          constituency="ONGOLE"
          category=""
          status=""
          q=""
          options={options}
          onStateChange={() => undefined}
          onConstituencyChange={() => undefined}
          onCategoryChange={() => undefined}
          onStatusChange={() => undefined}
          onQueryChange={onQueryChange}
        />
      </form>,
    );
    await user.type(screen.getByPlaceholderText(/Scheme ID/), "road");
    expect(onQueryChange).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Clear search" })).toBeInTheDocument();
  });

  it("submits on Search button and Enter", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn((event: SubmitEvent) => event.preventDefault());
    const onQueryChange = vi.fn();
    render(
      <form onSubmit={onSubmit}>
        <SearchFilters
          stateFilter="Andhra Pradesh"
          constituency=""
          category=""
          status=""
          q="school"
          options={options}
          onStateChange={() => undefined}
          onConstituencyChange={() => undefined}
          onCategoryChange={() => undefined}
          onStatusChange={() => undefined}
          onQueryChange={onQueryChange}
        />
      </form>,
    );
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    await user.type(screen.getByPlaceholderText(/Scheme ID/), "{Enter}");
    expect(onSubmit).toHaveBeenCalledTimes(2);
  });

  it("keeps state and constituency when the query changes", async () => {
    const user = userEvent.setup();
    render(
      <form>
        <SearchFilters
          stateFilter="Andhra Pradesh"
          constituency="ONGOLE"
          category="Roads"
          status="Ongoing"
          q=""
          options={options}
          onStateChange={() => undefined}
          onConstituencyChange={() => undefined}
          onCategoryChange={() => undefined}
          onStatusChange={() => undefined}
          onQueryChange={() => undefined}
        />
      </form>,
    );
    await user.type(screen.getByPlaceholderText(/Scheme ID/), "road");
    expect(screen.getByRole("combobox", { name: "State" })).toHaveTextContent("Andhra Pradesh");
    expect(screen.getByRole("combobox", { name: "Constituency" })).toHaveTextContent("ONGOLE");
    expect(screen.getByRole("combobox", { name: "Category" })).toHaveTextContent("Roads");
    expect(screen.getByRole("combobox", { name: "Status" })).toHaveTextContent("Ongoing");
  });

  it("clears the text query through Clear search", async () => {
    const user = userEvent.setup();
    const onQueryChange = vi.fn();
    const onClearQuery = vi.fn();
    render(
      <form>
        <SearchFilters
          stateFilter="Andhra Pradesh"
          constituency="ONGOLE"
          category="Roads"
          status="Ongoing"
          q="road"
          options={options}
          onStateChange={() => undefined}
          onConstituencyChange={() => undefined}
          onCategoryChange={() => undefined}
          onStatusChange={() => undefined}
          onQueryChange={onQueryChange}
          onClearQuery={onClearQuery}
        />
      </form>,
    );
    await user.click(screen.getByRole("button", { name: "Clear search" }));
    expect(onQueryChange).toHaveBeenCalledWith("");
    expect(onClearQuery).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("combobox", { name: "State" })).toHaveTextContent("Andhra Pradesh");
    expect(screen.getByRole("combobox", { name: "Constituency" })).toHaveTextContent("ONGOLE");
  });
});
