import type { ReactNode } from "react";

import { FeatureExplanation } from "@/components/system/FeatureExplanation";

export function PageHeader({
  kicker,
  title,
  explanation,
  actions,
  children,
}: {
  kicker?: string;
  title: string;
  explanation?: string;
  actions?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="svk-reveal flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0 max-w-4xl">
        {kicker ? <p className="svk-kicker">{kicker}</p> : null}
        <h1 className="svk-display mt-1 text-[1.7rem] font-semibold leading-tight text-[var(--navy)] sm:text-[2rem]">
          {title}
        </h1>
        {explanation ? <FeatureExplanation text={explanation} /> : null}
        {children}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
