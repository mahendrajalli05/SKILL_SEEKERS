import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams("mode=hybrid"),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: string; href: string }) => <a href={href}>{children}</a>,
}));

import { NAV_GROUPS, navItemIsActive } from "@/components/AppHeader";
import { StyledSelect } from "@/components/ui/StyledSelect";
import { FEATURE_EXPLANATIONS, ML_NOT_FRAUD, SYSTEM_PIPELINE } from "@/lib/explanations";

describe("Final UI/UX visual transformation V3", () => {
  it("uses hub navigation instead of listing every module", () => {
    const sections = NAV_GROUPS.map((group) => group.label);
    const labels = NAV_GROUPS.flatMap((group) => group.items.map((item) => item.label));
    expect(sections).toEqual([
      "OVERVIEW",
      "PROJECTS",
      "INVESTIGATION",
      "EVIDENCE",
      "VERIFICATION",
      "ANALYTICS",
      "PLANNING",
      "LIFECYCLE",
      "AI & MODELS",
      "CONTEXT",
      "ASSESSMENT",
      "DEMO",
    ]);
    expect(labels).toContain("Projects");
    expect(labels).toContain("Evidence Center");
    expect(labels).toContain("Cost Intelligence");
    expect(labels).toContain("Geospatial Verification");
    expect(labels).toContain("Project Prioritization");
    expect(labels).toContain("ML Signals");
    expect(labels).toContain("Investigation Copilot");
    expect(labels).not.toContain("Search");
    expect(labels).not.toContain("Projects / Investigation");
    expect(labels).not.toContain("Intelligence");
    expect(labels).not.toContain("Evidence & Verification");
    expect(sections.join(" ")).not.toContain("SIH26102");
  });

  it("treats project routes as part of Projects and investigation routes as Investigation", () => {
    expect(navItemIsActive("/projects/12", { href: "/search", match: "projects" })).toBe(true);
    expect(navItemIsActive("/projects/12/investigate", { href: "/search", match: "projects" })).toBe(false);
    expect(navItemIsActive("/investigate", { href: "/investigate", match: "investigate" })).toBe(true);
    expect(navItemIsActive("/geospatial", { href: "/geospatial", match: "prefix" })).toBe(true);
    expect(navItemIsActive("/need-impact", { href: "/need-impact", match: "prefix" })).toBe(true);
    expect(navItemIsActive("/analytics/cost", { href: "/analytics/cost", match: "prefix" })).toBe(true);
  });

  it("keeps one-line explanations and ML governance language", () => {
    expect(FEATURE_EXPLANATIONS.geo).toMatch(/geographically consistent/i);
    expect(FEATURE_EXPLANATIONS.ml).toMatch(/training distribution/i);
    expect(ML_NOT_FRAUD).toBe("ML anomaly score is not a fraud probability.");
    expect(SYSTEM_PIPELINE).toEqual(["DISCOVER", "UNDERSTAND", "VERIFY", "ANALYSE", "ASSESS", "DECIDE"]);
  });

  it("renders a readable styled select menu", async () => {
    const user = userEvent.setup();
    let value = "other";
    render(
      <StyledSelect
        label="Issue category"
        value={value}
        onChange={(next) => {
          value = next;
        }}
        options={[
          { value: "work_quality", label: "Work quality" },
          { value: "other", label: "Other" },
        ]}
      />,
    );
    await user.click(screen.getByRole("combobox", { name: "Issue category" }));
    expect(screen.getByRole("option", { name: "Work quality" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Other" })).toHaveAttribute("aria-selected", "true");
  });
});
