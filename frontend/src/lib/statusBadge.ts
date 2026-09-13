export type BadgeTone =
  | "real"
  | "hybrid"
  | "synthetic"
  | "neutral"
  | "positive"
  | "attention"
  | "muted"
  | "navy";

export type BadgeKind =
  | "REAL"
  | "HYBRID"
  | "SYNTHETIC"
  | "DEMO"
  | "CONSISTENT"
  | "MISMATCH"
  | "INCONCLUSIVE"
  | "PROCEED"
  | "HOLD"
  | "INSPECT"
  | "REVIEW"
  | "MONITOR"
  | "NEED MORE INFORMATION"
  | "NEED_MORE_INFORMATION"
  | "UNAVAILABLE"
  | "NOT_ASSESSABLE"
  | "INSUFFICIENT_EVIDENCE"
  | "UNKNOWN";

const TONE_CLASS: Record<BadgeTone, string> = {
  real: "border-[var(--signal)] bg-[var(--signal-soft)] text-[var(--signal)]",
  hybrid: "border-[var(--saffron)] bg-[var(--saffron-soft)] text-[var(--saffron)]",
  synthetic: "border-[var(--danger)] bg-[var(--danger-soft)] text-[var(--danger)]",
  neutral: "border-[var(--line)] bg-[var(--surface-2)] text-[var(--ink)]",
  positive: "border-[var(--success)] bg-[var(--success-soft)] text-[var(--success)]",
  attention: "border-[var(--hold)] bg-[var(--hold-soft)] text-[var(--hold)]",
  muted: "border-[var(--line)] bg-[var(--navy-soft)] text-[var(--muted)]",
  navy: "border-[var(--indigo)] bg-[var(--indigo-soft)] text-[var(--navy)]",
};

export function normalizeBadgeKind(value: string | null | undefined): BadgeKind | null {
  const raw = (value ?? "").trim();
  if (!raw) return null;
  const upper = raw.replaceAll("_", " ").toUpperCase();
  if (upper === "REAL" || upper === "REAL DATA") return "REAL";
  if (upper === "HYBRID" || upper === "HYBRID DEMO" || upper === "HYBRID DEMO MODE") return "HYBRID";
  if (upper === "SYNTHETIC") return "SYNTHETIC";
  if (upper === "DEMO") return "DEMO";
  if (upper === "CONSISTENT") return "CONSISTENT";
  if (upper === "MISMATCH") return "MISMATCH";
  if (upper === "INCONCLUSIVE") return "INCONCLUSIVE";
  if (upper === "PROCEED") return "PROCEED";
  if (upper === "HOLD") return "HOLD";
  if (upper === "INSPECT" || upper === "INVESTIGATE") return "INSPECT";
  if (upper === "REVIEW") return "REVIEW";
  if (upper === "MONITOR") return "MONITOR";
  if (upper === "NEED MORE INFORMATION" || upper === "NEED MORE INFO") return "NEED MORE INFORMATION";
  if (upper === "UNAVAILABLE") return "UNAVAILABLE";
  if (upper === "NOT ASSESSABLE") return "NOT_ASSESSABLE";
  if (upper === "INSUFFICIENT EVIDENCE") return "INSUFFICIENT_EVIDENCE";
  if (upper === "UNKNOWN") return "UNKNOWN";
  return null;
}

export function badgeLabel(kind: BadgeKind): string {
  switch (kind) {
    case "REAL":
      return "REAL";
    case "HYBRID":
      return "HYBRID";
    case "SYNTHETIC":
      return "SYNTHETIC";
    case "DEMO":
      return "DEMO";
    case "CONSISTENT":
      return "CONSISTENT";
    case "MISMATCH":
      return "MISMATCH";
    case "INCONCLUSIVE":
      return "INCONCLUSIVE";
    case "PROCEED":
      return "PROCEED";
    case "HOLD":
      return "HOLD";
    case "INSPECT":
      return "INSPECT";
    case "REVIEW":
      return "REVIEW";
    case "MONITOR":
      return "MONITOR";
    case "NEED MORE INFORMATION":
    case "NEED_MORE_INFORMATION":
      return "NEED MORE INFORMATION";
    case "UNAVAILABLE":
      return "UNAVAILABLE";
    case "NOT_ASSESSABLE":
      return "NOT ASSESSABLE";
    case "INSUFFICIENT_EVIDENCE":
      return "INSUFFICIENT EVIDENCE";
    case "UNKNOWN":
      return "UNKNOWN";
  }
}

export function badgeTone(kind: BadgeKind): BadgeTone {
  switch (kind) {
    case "REAL":
      return "real";
    case "HYBRID":
      return "hybrid";
    case "SYNTHETIC":
    case "DEMO":
      return "synthetic";
    case "CONSISTENT":
    case "PROCEED":
      return "positive";
    case "MISMATCH":
    case "HOLD":
      return "attention";
    case "INSPECT":
    case "REVIEW":
      return "navy";
    case "INCONCLUSIVE":
    case "MONITOR":
    case "NEED MORE INFORMATION":
    case "NEED_MORE_INFORMATION":
    case "UNAVAILABLE":
    case "NOT_ASSESSABLE":
    case "INSUFFICIENT_EVIDENCE":
    case "UNKNOWN":
      return "muted";
  }
}

export function badgeClassName(kind: BadgeKind): string {
  return TONE_CLASS[badgeTone(kind)];
}
