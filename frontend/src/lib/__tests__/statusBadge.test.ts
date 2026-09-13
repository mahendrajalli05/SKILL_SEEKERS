import { describe, expect, it } from "vitest";

import { badgeLabel, badgeTone, normalizeBadgeKind } from "@/lib/statusBadge";

describe("status badges", () => {
  it("maps REAL, HYBRID, and SYNTHETIC without treating them as equivalent", () => {
    expect(normalizeBadgeKind("REAL")).toBe("REAL");
    expect(normalizeBadgeKind("HYBRID DEMO")).toBe("HYBRID");
    expect(normalizeBadgeKind("SYNTHETIC")).toBe("SYNTHETIC");
    expect(normalizeBadgeKind("DEMO")).toBe("DEMO");
    expect(badgeTone("REAL")).toBe("real");
    expect(badgeTone("HYBRID")).toBe("hybrid");
    expect(badgeTone("SYNTHETIC")).toBe("synthetic");
  });

  it("uses restrained labels for officer recommendations", () => {
    expect(badgeLabel("PROCEED")).toBe("PROCEED");
    expect(badgeLabel("HOLD")).toBe("HOLD");
    expect(badgeLabel("INSPECT")).toBe("INSPECT");
    expect(badgeLabel("REVIEW")).toBe("REVIEW");
    expect(badgeLabel("MONITOR")).toBe("MONITOR");
    expect(badgeLabel("NEED MORE INFORMATION")).toBe("NEED MORE INFORMATION");
  });

  it("maps evidence comparison states", () => {
    expect(normalizeBadgeKind("consistent")).toBe("CONSISTENT");
    expect(normalizeBadgeKind("mismatch")).toBe("MISMATCH");
    expect(normalizeBadgeKind("inconclusive")).toBe("INCONCLUSIVE");
    expect(badgeTone("CONSISTENT")).toBe("positive");
    expect(badgeTone("INCONCLUSIVE")).toBe("muted");
  });
});
