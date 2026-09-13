"use client";

import { FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { InvestigationCopilotPanel } from "@/components/InvestigationCopilotPanel";
import { ProjectSelector } from "@/components/system/ProjectSelector";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { parseDataMode, withModePath } from "@/lib/display";
import type { ProjectSearchItem } from "@/lib/types";

function projectIdFromPath(pathname: string): number | null {
  const match = pathname.match(/^\/projects\/(\d+)/);
  if (!match) return null;
  const id = Number(match[1]);
  return Number.isFinite(id) ? id : null;
}

export function CopilotDrawer() {
  const pathname = usePathname() || "/";
  const searchParams = useSearchParams();
  const router = useRouter();
  const mode = parseDataMode(searchParams.get("mode"));
  const pathId = projectIdFromPath(pathname);
  const [open, setOpen] = useState(false);
  const [picked, setPicked] = useState<ProjectSearchItem | null>(null);
  const projectId = pathId ?? picked?.id ?? null;
  const docked = pathname.includes("/investigate");

  useEffect(() => {
    if (pathId) setPicked(null);
  }, [pathId]);

  const goCopilot = (event: FormEvent) => {
    event.preventDefault();
    if (projectId) {
      router.push(withModePath(`/projects/${projectId}/investigate#copilot`, mode));
      setOpen(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="fixed bottom-5 right-5 z-40 rounded-full border border-[var(--violet)] bg-white px-4 py-3 text-sm font-semibold tracking-[0.08em] text-[var(--violet)] shadow-lg"
        onClick={() => setOpen(true)}
      >
        ✦ COPILOT
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 flex justify-end bg-[rgba(27,42,61,0.28)]">
          <aside className="flex h-full w-full max-w-lg flex-col overflow-y-auto bg-[var(--shell)] p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="svk-kicker">Assistance</p>
                <h2 className="svk-display text-2xl font-semibold text-[var(--navy)]">Investigation Copilot</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">{FEATURE_EXPLANATIONS.copilot}</p>
              </div>
              <button type="button" className="svk-btn" onClick={() => setOpen(false)}>
                Close
              </button>
            </div>
            {docked && pathId ? (
              <p className="mt-4 text-sm">
                Copilot is already docked on this investigation. Use the side panel, or continue here.
              </p>
            ) : null}
            {projectId ? (
              <div className="mt-4">
                <InvestigationCopilotPanel projectId={projectId} mode={mode} />
                <form onSubmit={goCopilot} className="mt-3">
                  <button type="submit" className="svk-btn">
                    Open in Investigation Workspace
                  </button>
                </form>
              </div>
            ) : (
              <div className="mt-4">
                <ProjectSelector mode={mode} onSelect={setPicked} heading="Choose a project first" />
              </div>
            )}
          </aside>
        </div>
      ) : null}
    </>
  );
}
