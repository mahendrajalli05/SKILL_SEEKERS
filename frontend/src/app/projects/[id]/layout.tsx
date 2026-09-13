import { Suspense, type ReactNode } from "react";

import { ProjectSubNav } from "@/components/ProjectSubNav";
import { DemoWorkflowBanner } from "@/components/DemoWorkflowBanner";

export default function ProjectLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<p className="text-sm text-[var(--muted)]">Loading project…</p>}>
      <ProjectSubNav />
      <DemoWorkflowBanner />
      {children}
    </Suspense>
  );
}
