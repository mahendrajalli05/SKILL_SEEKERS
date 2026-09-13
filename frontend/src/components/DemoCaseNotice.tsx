"use client";

import { StatusBadge } from "@/components/ui/StatusBadge";
import { DEMO_CASE_NOTICE } from "@/lib/display";

export function DemoCaseNotice({
  caseName,
  notice,
}: {
  caseName?: string;
  notice?: string | null;
}) {
  return (
    <section className="border border-[var(--saffron)] bg-[var(--saffron-soft)] p-4">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge kind="DEMO" />
        <StatusBadge kind="HYBRID" />
        <StatusBadge kind="SYNTHETIC" />
        <StatusBadge label="CONTROLLED PROTOTYPE" />
        {caseName ? <p className="text-sm font-semibold text-[var(--navy)]">{caseName}</p> : null}
      </div>
      <p className="mt-2 text-sm text-[var(--navy)]">{notice || DEMO_CASE_NOTICE}</p>
    </section>
  );
}
