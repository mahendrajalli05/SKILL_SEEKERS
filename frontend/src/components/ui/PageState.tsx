export type PageStateKind =
  | "loading"
  | "unavailable"
  | "inconclusive"
  | "insufficient"
  | "error"
  | "empty";

const COPY: Record<PageStateKind, { title: string; fallback: string }> = {
  loading: { title: "Loading", fallback: "Loading…" },
  unavailable: { title: "Unavailable", fallback: "This information is unavailable." },
  inconclusive: { title: "Inconclusive", fallback: "The available evidence is inconclusive." },
  insufficient: {
    title: "Insufficient Evidence",
    fallback: "There is insufficient evidence to assess this item.",
  },
  error: { title: "API Error", fallback: "The request could not be completed." },
  empty: { title: "No Results", fallback: "No matching records were found." },
};

export function PageState({
  kind,
  title,
  message,
  compact = false,
}: {
  kind: PageStateKind;
  title?: string;
  message?: string;
  compact?: boolean;
}) {
  const copy = COPY[kind];
  return (
    <div
      role={kind === "error" ? "alert" : kind === "loading" ? "status" : "note"}
      aria-live={kind === "loading" || kind === "error" ? "polite" : undefined}
      className={`border p-4 ${
        kind === "error"
          ? "border-[var(--saffron)] bg-[var(--surface)]"
          : "border-[var(--line)] bg-[var(--surface)]"
      }`}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        {title ?? copy.title}
      </p>
      <p className={`mt-1 text-sm ${kind === "error" ? "text-[var(--saffron)]" : "text-[var(--muted)]"}`}>
        {message ?? copy.fallback}
      </p>
    </div>
  );
}
