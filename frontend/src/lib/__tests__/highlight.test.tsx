import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HighlightedText } from "@/lib/highlight";

describe("HighlightedText", () => {
  it("wraps a case-insensitive match", () => {
    const { container } = render(<HighlightedText text="Construction of roads" query="ROADS" />);
    expect(container.querySelector("mark")?.textContent).toBe("roads");
    expect(container.textContent).toBe("Construction of roads");
  });

  it("does not highlight when the query is empty", () => {
    const { container } = render(<HighlightedText text="Construction of roads" query="   " />);
    expect(container.querySelector("mark")).toBeNull();
  });
});
