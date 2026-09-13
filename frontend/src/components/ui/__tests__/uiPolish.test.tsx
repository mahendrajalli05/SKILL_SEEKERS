import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageState } from "@/components/ui/PageState";
import { SectionCard } from "@/components/ui/SectionCard";
import { WorkspaceTabs } from "@/components/ui/WorkspaceTabs";
import { LazyDisclosure } from "@/components/ui/LazyDisclosure";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("StatusBadge", () => {
  it("renders REAL, HYBRID, and SYNTHETIC", () => {
    const { rerender } = render(<StatusBadge kind="REAL" />);
    expect(screen.getByText("REAL")).toBeInTheDocument();
    rerender(<StatusBadge kind="HYBRID" />);
    expect(screen.getByText("HYBRID")).toBeInTheDocument();
    rerender(<StatusBadge kind="SYNTHETIC" />);
    expect(screen.getByText("SYNTHETIC")).toBeInTheDocument();
  });
});

describe("PageState", () => {
  it("covers loading, empty, error, unavailable, and inconclusive", () => {
    const { rerender } = render(<PageState kind="loading" message="Loading search results…" />);
    expect(screen.getByText("Loading search results…")).toBeInTheDocument();
    rerender(<PageState kind="empty" message="No matching projects found" />);
    expect(screen.getByText("No Results")).toBeInTheDocument();
    rerender(<PageState kind="error" message="API request failed" />);
    expect(screen.getByText("API Error")).toBeInTheDocument();
    rerender(<PageState kind="unavailable" />);
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    rerender(<PageState kind="inconclusive" />);
    expect(screen.getByText("Inconclusive")).toBeInTheDocument();
    rerender(<PageState kind="insufficient" />);
    expect(screen.getByText("Insufficient Evidence")).toBeInTheDocument();
  });
});

describe("SectionCard", () => {
  it("renders a heading for screen readers", () => {
    render(
      <SectionCard title="Officer dashboard" description="Pilot scope">
        Content
      </SectionCard>,
    );
    expect(screen.getByRole("heading", { name: "Officer dashboard" })).toBeInTheDocument();
  });
});

describe("WorkspaceTabs", () => {
  it("shows only the active tab panel", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    const user = userEvent.setup();
    render(
      <WorkspaceTabs
        ariaLabel="Investigation workspace sections"
        tabs={[
          { id: "why", label: "Why?", content: <p>Why content</p> },
          { id: "copilot", label: "Copilot", content: <p>Copilot content</p> },
        ]}
      />,
    );
    expect(screen.getByText("Why content")).toBeInTheDocument();
    expect(screen.queryByText("Copilot content")).toBeNull();
    await user.click(screen.getByRole("tab", { name: "Copilot" }));
    expect(screen.getByText("Copilot content")).toBeInTheDocument();
    expect(screen.queryByText("Why content")).toBeNull();
  });
});

describe("LazyDisclosure", () => {
  it("does not mount children until opened", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    const user = userEvent.setup();
    render(
      <LazyDisclosure title="DOCUMENTS" summary="Open to load documents.">
        <p>Document panel loaded</p>
      </LazyDisclosure>,
    );
    expect(screen.queryByText("Document panel loaded")).toBeNull();
    expect(screen.getByText("Open to load documents.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /DOCUMENTS/ }));
    expect(screen.getByText("Document panel loaded")).toBeInTheDocument();
  });
});
