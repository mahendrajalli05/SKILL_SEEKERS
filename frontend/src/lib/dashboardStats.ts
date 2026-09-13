import { fetchProjects, fetchScope } from "@/lib/api";
import { DEFAULT_PILOT_STATE, PILOT_LABEL, parseDataMode } from "@/lib/display";
import type { DataMode } from "@/lib/types";

export interface PilotCounts {
  total: number | null;
  future: number | null;
  ongoing: number | null;
  completed: number | null;
  pilotLabel: string;
  note: string;
}

function engineMode(mode: Exclude<DataMode, "SYNTHETIC">): "real" | "hybrid" {
  return mode === "REAL" ? "real" : "hybrid";
}

async function totalForQuery(
  mode: Exclude<DataMode, "SYNTHETIC">,
  status?: string,
): Promise<{ total: number; note: string } | null> {
  try {
    const body = await fetchProjects({
      page: 1,
      page_size: 1,
      state: DEFAULT_PILOT_STATE,
      apply_pilot_scope: true,
      status,
      mode: engineMode(mode),
    });
    return { total: body.total, note: body.note };
  } catch {
    return null;
  }
}

export async function fetchPilotCounts(
  modeValue: string | null | undefined,
): Promise<PilotCounts> {
  const mode = parseDataMode(modeValue);
  const [scope, all, unsanctioned, sanctioned, ongoing, completed] = await Promise.all([
    fetchScope().catch(() => null),
    totalForQuery(mode),
    totalForQuery(mode, "Unsanctioned"),
    totalForQuery(mode, "Sanctioned"),
    totalForQuery(mode, "Ongoing"),
    totalForQuery(mode, "Completed"),
  ]);
  const future =
    unsanctioned == null || sanctioned == null ? null : unsanctioned.total + sanctioned.total;
  return {
    total: all?.total ?? null,
    future,
    ongoing: ongoing?.total ?? null,
    completed: completed?.total ?? null,
    pilotLabel: scope?.pilot_label ?? PILOT_LABEL,
    note: all?.note ?? "",
  };
}
