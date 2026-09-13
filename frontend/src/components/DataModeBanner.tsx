"use client";

import { StatusBadge } from "@/components/ui/StatusBadge";
import type { DataMode } from "@/lib/types";
import {
  HYBRID_DEMO_NOTICE,
  PILOT_LABEL,
  PROTOTYPE_SIMULATION_NOTICE,
  REAL_DATA_NOTICE,
  dataModeLabel,
} from "@/lib/display";

export function DataModeBanner({
  mode,
  hasHybridEnrichment,
  hybridNotice,
  onModeChange,
}: {
  mode: DataMode;
  hasHybridEnrichment?: boolean;
  hybridNotice?: string | null;
  onModeChange?: (mode: DataMode) => void;
}) {
  const current = dataModeLabel(mode);
  const compact = current === "REAL" ? "Andhra Pradesh Pilot" : "Controlled prototype";
  return (
    <details className="svk-env max-w-xl" data-mode={current} aria-label="Data environment">
      <summary>
        <span
          className={`h-2 w-2 rounded-full ${current === "REAL" ? "bg-[var(--signal)]" : "bg-[var(--saffron)]"}`}
          aria-hidden
        />
        <span className="text-sm font-semibold tracking-[0.08em] text-[var(--navy)]">
          {current === "REAL" ? "REAL DATA" : "HYBRID DEMO"}
        </span>
        <StatusBadge kind={current === "REAL" ? "REAL" : "HYBRID"} />
        {current !== "REAL" ? <StatusBadge kind="SYNTHETIC" /> : null}
        <span className="text-xs text-[var(--muted)]">{compact}</span>
      </summary>
      <div className="svk-env-body space-y-2 text-sm">
        <p>{current === "REAL" ? REAL_DATA_NOTICE : hybridNotice || HYBRID_DEMO_NOTICE}</p>
        {current !== "REAL" ? <p>{PROTOTYPE_SIMULATION_NOTICE}</p> : null}
        <p className="text-xs text-[var(--muted)]">{PILOT_LABEL}</p>
        {onModeChange ? (
          <div className="flex flex-wrap gap-2 pt-1">
            <button type="button" className="svk-btn" onClick={() => onModeChange("REAL")}>
              REAL DATA
            </button>
            <button type="button" className="svk-btn" onClick={() => onModeChange("HYBRID")}>
              HYBRID DEMO
            </button>
          </div>
        ) : null}
        {hasHybridEnrichment && current === "HYBRID" ? (
          <p className="text-xs uppercase tracking-wide text-[var(--saffron)]">
            This work has SYNTHETIC prototype enrichment
          </p>
        ) : null}
      </div>
    </details>
  );
}
