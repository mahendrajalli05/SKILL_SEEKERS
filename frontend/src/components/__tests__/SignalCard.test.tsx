import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SignalCard } from "@/components/SignalCard";

describe("SignalCard", () => {
  it("shows INSUFFICIENT_EVIDENCE instead of 0", () => {
    render(
      <SignalCard
        title="Time anomaly"
        score={0}
        state="INSUFFICIENT_EVIDENCE"
        explanation="Time Intelligence unavailable because verified execution dates are not present in the current real dataset."
      />,
    );
    expect(screen.getAllByText("INSUFFICIENT EVIDENCE").length).toBeGreaterThan(0);
    expect(screen.getByText(/verified execution dates/)).toBeInTheDocument();
    expect(screen.queryByText("0")).toBeNull();
  });
});
