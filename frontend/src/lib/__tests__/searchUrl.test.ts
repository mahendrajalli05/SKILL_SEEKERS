import { describe, expect, it } from "vitest";

import { DEFAULT_PILOT_STATE } from "@/lib/display";
import { buildSearchQueryString, parseSearchUrl } from "@/lib/searchUrl";

describe("search URL state", () => {
  it("parses text query, filters, and page", () => {
    const parsed = parseSearchUrl(
      new URLSearchParams(
        "q=road&state=Andhra%20Pradesh&constituency=ONGOLE&category=Roads&status=Ongoing&page=2&mode=real",
      ),
    );
    expect(parsed.q).toBe("road");
    expect(parsed.state).toBe("Andhra Pradesh");
    expect(parsed.constituency).toBe("ONGOLE");
    expect(parsed.category).toBe("Roads");
    expect(parsed.status).toBe("Ongoing");
    expect(parsed.page).toBe(2);
    expect(parsed.mode).toBe("real");
  });

  it("defaults to the AP pilot when state is omitted", () => {
    const parsed = parseSearchUrl(new URLSearchParams());
    expect(parsed.state).toBe(DEFAULT_PILOT_STATE);
    expect(parsed.q).toBe("");
    expect(parsed.page).toBe(1);
  });

  it("omits empty text query and page 1 from the query string", () => {
    const qs = buildSearchQueryString({
      q: "  ",
      state: "Andhra Pradesh",
      constituency: "",
      category: "",
      status: "",
      page: 1,
      mode: "hybrid",
      scheme_id: "",
      internal_project_id: "",
    });
    expect(qs).not.toContain("q=");
    expect(qs).toContain("state=Andhra+Pradesh");
    expect(qs).not.toContain("page=");
  });
});
