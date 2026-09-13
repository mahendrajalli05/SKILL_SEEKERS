import {
  badgeClassName,
  badgeLabel,
  normalizeBadgeKind,
  type BadgeKind,
} from "@/lib/statusBadge";

export function StatusBadge({
  value,
  kind,
  label,
}: {
  value?: string | null;
  kind?: BadgeKind;
  label?: string;
}) {
  const resolved = kind ?? normalizeBadgeKind(value);
  if (!resolved && !label && !value) {
    return null;
  }
  const text = label ?? (resolved ? badgeLabel(resolved) : String(value));
  const classes = resolved
    ? badgeClassName(resolved)
    : "border-[var(--line)] bg-white text-[var(--ink)]";
  return (
    <span
      className={`inline-flex items-center border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${classes}`}
    >
      {text}
    </span>
  );
}
