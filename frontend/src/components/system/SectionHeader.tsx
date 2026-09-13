import type { ReactNode } from "react";

import { FeatureExplanation } from "@/components/system/FeatureExplanation";

export function SectionHeader({
  title,
  explanation,
  actions,
}: {
  title: string;
  explanation?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="max-w-3xl">
        <h2 className="svk-display text-[1.35rem] font-semibold text-[var(--navy)] sm:text-[1.5rem]">{title}</h2>
        {explanation ? <FeatureExplanation text={explanation} /> : null}
      </div>
      {actions}
    </div>
  );
}
