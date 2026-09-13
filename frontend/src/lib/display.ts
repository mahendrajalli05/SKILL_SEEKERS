import type { DataMode, ProjectRiskResponse } from "./types";

export const UNAVAILABLE_REAL_LABEL = "Unavailable in current public extract";
export const NOT_ASSESSABLE_LABEL = "Not assessable";
export const SCHEME_ID_NOTE =
  "Internal SARVSAKSHI application identifier — not an official MPLADS Work ID.";
export const HYBRID_DEMO_NOTICE =
  "HYBRID DEMO — Base project data comes from a real MPLADS extract. Fields marked SYNTHETIC are simulated prototype enrichment and are not official MPLADS records.";
export const PROTOTYPE_SIMULATION_NOTICE =
  "Prototype simulation: some fields are synthetic and are not official MPLADS records.";
export const DEMO_CASE_NOTICE =
  "Controlled prototype scenario. Some values are synthetic and are not official MPLADS records. DEMO / SYNTHETIC / CONTROLLED PROTOTYPE evidence fixtures are not official MPLADS evidence.";
export const REAL_DATA_NOTICE =
  "REAL DATA — Showing observed MPLADS extract fields only. Missing government fields are listed as unavailable in the current public extract. Synthetic enrichment is not used.";
export const PILOT_LABEL = "Current Pilot: Andhra Pradesh";
export const SELECT_STATE_FIRST = "Select state first";
export const DEFAULT_PILOT_STATE = "Andhra Pradesh";
export const DEFAULT_DATA_MODE: DataMode = "HYBRID";

export const TIME_UNAVAILABLE_MESSAGE =
  "Time Intelligence unavailable because verified execution dates are not present in the current real dataset.";

export function displayText(value: string | null | undefined): string {
  const text = value?.trim();
  return text ? text : UNAVAILABLE_REAL_LABEL;
}

export function formatAllocation(amount: number | null | undefined): string {
  if (amount == null) {
    return UNAVAILABLE_REAL_LABEL;
  }
  return `${amount.toLocaleString("en-IN")} (unit unspecified)`;
}

export function formatDate(value: string | null | undefined): string {
  return displayText(value);
}

export function isUnassessedState(state: string | null | undefined): boolean {
  const value = (state ?? "").toUpperCase();
  return (
    value === "NOT_ASSESSABLE" ||
    value === "UNAVAILABLE" ||
    value === "INCONCLUSIVE" ||
    value === "INSUFFICIENT_EVIDENCE" ||
    value === "NOT_YET_INTEGRATED"
  );
}

export function displayBoundedScore(
  score: number | null | undefined,
  state?: string | null,
): { label: string; assessed: boolean } {
  if (score == null || isUnassessedState(state)) {
    if (!state) {
      return { label: NOT_ASSESSABLE_LABEL, assessed: false };
    }
    if (state.toUpperCase() === "NOT_ASSESSABLE") {
      return { label: NOT_ASSESSABLE_LABEL, assessed: false };
    }
    return { label: state.replaceAll("_", " "), assessed: false };
  }
  return { label: String(score), assessed: true };
}

export function displayInvestigationPriority(
  risk: ProjectRiskResponse | null | undefined,
): { label: string; assessed: boolean; numeric: number | null } {
  if (!risk) {
    return { label: NOT_ASSESSABLE_LABEL, assessed: false, numeric: null };
  }
  if (risk.explanation_type === "INSUFFICIENT_EVIDENCE") {
    return {
      label: "Not assessed — insufficient evidence",
      assessed: false,
      numeric: null,
    };
  }
  return {
    label: String(risk.investigation_priority),
    assessed: true,
    numeric: risk.investigation_priority,
  };
}

export function displayEvidenceConfidence(
  risk: ProjectRiskResponse | null | undefined,
): { label: string; assessed: boolean; numeric: number | null } {
  if (!risk) {
    return { label: NOT_ASSESSABLE_LABEL, assessed: false, numeric: null };
  }
  if (risk.explanation_type === "INSUFFICIENT_EVIDENCE") {
    return {
      label: "Not assessed — insufficient evidence",
      assessed: false,
      numeric: null,
    };
  }
  return {
    label: String(risk.evidence_confidence),
    assessed: true,
    numeric: risk.evidence_confidence,
  };
}

export function dataModeLabel(mode: DataMode | string | null | undefined): DataMode {
  if (mode === "HYBRID" || mode === "SYNTHETIC" || mode === "REAL") {
    return mode;
  }
  return "HYBRID";
}

export function parseDataMode(value: string | null | undefined): Exclude<DataMode, "SYNTHETIC"> {
  const text = (value ?? "").trim().toLowerCase();
  if (text === "real" || text === "real_data") {
    return "REAL";
  }
  return "HYBRID";
}

export function recommendedActionLabel(action: string | null | undefined): string {
  switch ((action ?? "").toUpperCase()) {
    case "MONITOR":
      return "Monitor";
    case "REVIEW":
      return "Review";
    case "INSPECT":
      return "Inspect";
    case "INVESTIGATE":
      return "Inspect";
    case "NEED_MORE_INFO":
    case "NEED_MORE_INFORMATION":
      return "Need more information";
    default:
      return displayText(action);
  }
}

export function officerActionLabel(action: string): string {
  switch (action) {
    case "confirm_concern":
      return "Confirm concern";
    case "dismiss":
      return "Dismiss";
    case "need_more_info":
    case "NEED_MORE_INFORMATION":
      return "Need more information";
    case "PROCEED":
      return "Proceed";
    case "HOLD":
      return "Hold";
    case "INSPECT":
      return "Inspect";
    default:
      return action;
  }
}

export function modeQuery(mode: Exclude<DataMode, "SYNTHETIC">): string {
  return mode === "REAL" ? "mode=real" : "mode=hybrid";
}

export function lifecycleFromStatus(status: string | null | undefined): string {
  const value = (status ?? "").trim().toLowerCase();
  if (value === "unsanctioned" || value === "sanctioned") return "FUTURE";
  if (value === "ongoing") return "ONGOING";
  if (value === "completed") return "COMPLETED";
  return "UNKNOWN";
}

export function withModePath(path: string, mode: Exclude<DataMode, "SYNTHETIC">): string {
  const hashIndex = path.indexOf("#");
  const hash = hashIndex >= 0 ? path.slice(hashIndex) : "";
  const withoutHash = hashIndex >= 0 ? path.slice(0, hashIndex) : path;
  const join = withoutHash.includes("?") ? "&" : "?";
  return `${withoutHash}${join}${modeQuery(mode)}${hash}`;
}
