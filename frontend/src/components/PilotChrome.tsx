"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { fetchScope } from "@/lib/api";
import type { DataMode } from "@/lib/types";
import { PILOT_LABEL, parseDataMode } from "@/lib/display";

export function PilotChrome() {
  const [pilotLabel, setPilotLabel] = useState(PILOT_LABEL);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const mode: Exclude<DataMode, "SYNTHETIC"> = parseDataMode(searchParams.get("mode"));

  useEffect(() => {
    fetchScope()
      .then((body) => setPilotLabel(body.pilot_label))
      .catch(() => setPilotLabel(PILOT_LABEL));
  }, []);

  const setMode = (next: Exclude<DataMode, "SYNTHETIC">) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("mode", next === "REAL" ? "real" : "hybrid");
    router.replace(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--navy)]">
      <p className="border border-[var(--line)] bg-white px-2 py-1">{pilotLabel}</p>
      <div className="flex overflow-hidden border border-[var(--line)] bg-white" role="group" aria-label="Data mode">
        <button
          type="button"
          aria-pressed={mode === "HYBRID"}
          className={`px-2 py-1 ${mode === "HYBRID" ? "bg-[var(--saffron-soft)] text-[var(--saffron)]" : "text-[var(--muted)]"}`}
          onClick={() => setMode("HYBRID")}
        >
          HYBRID DEMO
        </button>
        <button
          type="button"
          aria-pressed={mode === "REAL"}
          className={`px-2 py-1 ${mode === "REAL" ? "bg-[var(--signal-soft)] text-[var(--signal)]" : "text-[var(--muted)]"}`}
          onClick={() => setMode("REAL")}
        >
          REAL DATA
        </button>
      </div>
    </div>
  );
}
