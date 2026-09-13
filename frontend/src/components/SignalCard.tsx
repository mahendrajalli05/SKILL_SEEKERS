import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/system/ScoreDisplay";
import { displayBoundedScore } from "@/lib/display";

export function SignalCard({
  title,
  score,
  state,
  confidence,
  explanation,
  dataMode,
  flagged,
  compact = false,
}: {
  title: string;
  score?: number | null;
  state?: string | null;
  confidence?: number | null;
  explanation?: string | null;
  dataMode?: string | null;
  flagged?: boolean;
  compact?: boolean;
}) {
  const displayed = displayBoundedScore(score, state);
  return (
    <article className={`svk-card p-4 ${compact ? "" : ""}`} data-tone={flagged ? "saffron" : "signal"}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-sm font-semibold tracking-[0.08em] text-[var(--navy)]">{title}</h3>
        <StatusBadge value={state ?? (displayed.assessed ? "Assessed" : "Unavailable")} />
      </div>
      <p className="svk-mono mt-2 text-xl font-semibold text-[var(--navy)]">{displayed.label}</p>
      {displayed.assessed ? (
        <div className="mt-2">
          <ScoreBar value={score ?? null} />
        </div>
      ) : (
        <p className="mt-2 text-[0.65rem] uppercase tracking-wide text-[var(--muted)]">Unavailable</p>
      )}
      {!compact && confidence != null ? (
        <p className="mt-2 text-sm">Evidence confidence: {confidence}</p>
      ) : null}
      {explanation ? <p className={`mt-2 text-[var(--muted)] ${compact ? "text-xs" : "text-sm"}`}>{explanation}</p> : null}
      {dataMode ? <p className="mt-2 text-[0.65rem] uppercase tracking-wide text-[var(--muted)]">{dataMode}</p> : null}
    </article>
  );
}
