import { StatusBadge } from "@/components/ui/StatusBadge";

const TRACK = [
  { key: "FUTURE", label: "FUTURE" },
  { key: "PLANNING", label: "PLANNING" },
  { key: "ONGOING", label: "ONGOING" },
  { key: "MILESTONES", label: "MILESTONES" },
  { key: "COMPLETED", label: "COMPLETED" },
  { key: "FINAL_REVIEW", label: "FINAL REVIEW" },
] as const;

export function LifecycleTrack({
  current,
}: {
  current?: string | null;
}) {
  const value = (current ?? "UNKNOWN").toUpperCase();
  const stored = value === "FUTURE" || value === "ONGOING" || value === "COMPLETED" || value === "UNKNOWN";
  return (
    <section className="svk-panel p-5">
      <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">PROJECT LIFECYCLE</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Stored states are FUTURE, ONGOING, COMPLETED, or UNKNOWN. Planning, milestones, and final review are workflow labels.
      </p>
      <ol className="mt-5 flex flex-wrap items-center gap-2">
        {TRACK.map((step, index) => {
          const active =
            (step.key === "FUTURE" && value === "FUTURE") ||
            (step.key === "ONGOING" && value === "ONGOING") ||
            (step.key === "COMPLETED" && value === "COMPLETED") ||
            (step.key === "PLANNING" && value === "FUTURE") ||
            (step.key === "MILESTONES" && value === "ONGOING") ||
            (step.key === "FINAL_REVIEW" && value === "COMPLETED");
          return (
            <li key={step.key} className="flex items-center gap-2">
              <span
                className={`rounded-md border px-3 py-2 text-[0.68rem] font-semibold tracking-[0.12em] ${
                  active
                    ? "border-[var(--navy-fill)] bg-[var(--navy-fill)] text-white"
                    : "border-[var(--line)] bg-white text-[var(--navy)]"
                }`}
              >
                {step.label}
              </span>
              {index < TRACK.length - 1 ? (
                <span className="text-[var(--muted)]" aria-hidden>
                  →
                </span>
              ) : null}
            </li>
          );
        })}
      </ol>
      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge value={stored ? value : "UNKNOWN"} />
        {value === "UNKNOWN" ? <p className="text-sm text-[var(--muted)]">UNKNOWN remains UNKNOWN.</p> : null}
      </div>
    </section>
  );
}
