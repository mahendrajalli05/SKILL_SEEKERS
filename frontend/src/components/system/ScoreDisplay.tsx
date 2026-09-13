import { StatusBadge } from "@/components/ui/StatusBadge";

export function ScoreDisplay({
  label,
  value,
  assessed,
  note,
  kind = "priority",
}: {
  label: string;
  value: string;
  assessed?: boolean;
  note?: string;
  kind?: "priority" | "confidence" | "ml";
}) {
  const tone =
    kind === "ml" ? "text-[var(--violet)]" : kind === "confidence" ? "text-[var(--signal)]" : "text-[var(--saffron)]";
  return (
    <div className="min-w-0">
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className={`svk-mono mt-1 text-2xl font-semibold ${tone}`}>{value}</p>
      {assessed ? (
        <div className="mt-1">
          <StatusBadge label={kind === "priority" ? "Review priority" : kind === "ml" ? "Model signal" : "Confidence"} />
        </div>
      ) : null}
      {note ? <p className="mt-1 text-xs text-[var(--muted)]">{note}</p> : null}
    </div>
  );
}

export function ConfidenceDisplay({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return <ScoreDisplay label={label} value={value} kind="confidence" note={note} />;
}

export function ScoreBar({
  value,
  max = 100,
  label,
  tone = "signal",
}: {
  value: number | null | undefined;
  max?: number;
  label?: string;
  tone?: "signal" | "priority" | "ml" | "confidence";
}) {
  if (value == null || !Number.isFinite(value)) {
    return (
      <div>
        {label ? <p className="text-xs text-[var(--muted)]">{label}</p> : null}
        <div className="mt-1 h-1.5 w-full bg-[var(--navy-soft)]">
          <div className="h-full w-1/5 border-r border-dashed border-[var(--muted)]" />
        </div>
        <p className="mt-1 text-[0.65rem] uppercase tracking-wide text-[var(--muted)]">Not assessed</p>
      </div>
    );
  }
  const width = Math.max(0, Math.min(100, (value / max) * 100));
  const fill =
    tone === "ml"
      ? "bg-[var(--violet)]"
      : tone === "priority"
        ? "bg-[var(--saffron)]"
        : "bg-[var(--signal)]";
  return (
    <div>
      {label ? <p className="text-xs text-[var(--muted)]">{label}</p> : null}
      <div className="mt-1 h-1.5 w-full overflow-hidden bg-[var(--navy-soft)]">
        <div className={`svk-score-fill h-full ${fill}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
