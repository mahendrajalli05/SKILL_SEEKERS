"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { DataModeBanner } from "@/components/DataModeBanner";
import { PageHeader } from "@/components/system/PageHeader";
import { ProjectSelector } from "@/components/system/ProjectSelector";
import { PageState } from "@/components/ui/PageState";
import { parseDataMode, withModePath } from "@/lib/display";
import type { DataMode, ProjectSearchItem } from "@/lib/types";

export function ProjectFeaturePage({
  kicker,
  title,
  explanation,
  children,
}: {
  kicker: string;
  title: string;
  explanation: string;
  children: (projectId: number, mode: DataMode) => ReactNode;
}) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const mode = parseDataMode(searchParams.get("mode"));
  const raw = Number(searchParams.get("project") ?? "");
  const projectId = Number.isFinite(raw) && raw > 0 ? raw : null;
  const [selected, setSelected] = useState<ProjectSearchItem | null>(null);

  useEffect(() => {
    if (!projectId) setSelected(null);
  }, [projectId]);

  const choose = (item: ProjectSearchItem) => {
    setSelected(item);
    const params = new URLSearchParams(searchParams.toString());
    params.set("project", String(item.id));
    params.set("mode", mode === "REAL" ? "real" : "hybrid");
    router.replace(`?${params.toString()}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader kicker={kicker} title={title} explanation={explanation} />
      <DataModeBanner mode={mode} />
      <ProjectSelector mode={mode} selected={selected} onSelect={choose} />
      {projectId ? (
        children(projectId, mode)
      ) : (
        <PageState kind="empty" message="Select a project to open this capability." />
      )}
      {projectId ? (
        <p className="text-sm">
          <a className="underline" href={withModePath(`/projects/${projectId}`, mode)}>
            Open Project Digital Passport
          </a>
        </p>
      ) : null}
    </div>
  );
}
