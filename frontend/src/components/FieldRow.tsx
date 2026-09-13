import { StatusBadge } from "@/components/ui/StatusBadge";
import { displayText } from "@/lib/display";

export function FieldRow({
  label,
  value,
  hint,
  synthetic = false,
}: {
  label: string;
  value: string | number | null | undefined;
  hint?: string;
  synthetic?: boolean;
}) {
  const text = typeof value === "number" ? String(value) : displayText(value);
  const unavailable = text === "Unavailable in current public extract" || text === "Not assessable";
  return (
    <div className="grid min-w-0 gap-1 border-b border-[var(--line)] py-2 sm:grid-cols-[12rem_minmax(0,1fr)]">
      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</dt>
      <dd className="min-w-0">
        <span className={`break-words ${unavailable ? "text-[var(--muted)]" : ""}`}>{text}</span>
        {synthetic ? (
          <span className="ml-2">
            <StatusBadge kind="SYNTHETIC" />
          </span>
        ) : null}
        {hint ? <p className="mt-1 text-xs text-[var(--muted)]">{hint}</p> : null}
      </dd>
    </div>
  );
}
