import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  hint,
  tone = "signal",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "signal" | "saffron" | "success" | "indigo" | "violet";
}) {
  return (
    <article className="svk-metric svk-card" data-tone={tone === "saffron" ? "saffron" : tone === "success" ? "success" : tone === "indigo" ? "indigo" : tone === "violet" ? "violet" : "signal"}>
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">{label}</p>
      <div className="svk-mono mt-3 text-[2.15rem] font-semibold leading-none text-[var(--navy)]">{value}</div>
      {hint ? <p className="mt-2 text-xs text-[var(--muted)]">{hint}</p> : null}
    </article>
  );
}
