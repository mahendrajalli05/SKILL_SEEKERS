export function WorkflowStepper({
  steps,
  current,
  onSelect,
}: {
  steps: readonly string[];
  current: number;
  onSelect?: (index: number) => void;
}) {
  return (
    <ol className="flex flex-wrap gap-2 pb-1">
      {steps.map((step, index) => {
        const active = index === current;
        const done = index < current;
        return (
          <li key={step}>
            <button
              type="button"
              onClick={() => onSelect?.(index)}
              className={`flex min-w-0 flex-1 items-center gap-2 border px-3 py-2 text-left ${
                active
                  ? "border-[var(--navy-fill)] bg-[var(--navy-fill)] text-white"
                  : done
                    ? "border-[var(--success)] bg-[var(--success-soft)] text-[var(--navy)]"
                    : "border-[var(--line)] bg-white text-[var(--navy)]"
              }`}
              aria-current={active ? "step" : undefined}
            >
              <span className="svk-mono text-xs">{String(index + 1).padStart(2, "0")}</span>
              <span className="text-xs font-semibold tracking-[0.08em]">{step}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
