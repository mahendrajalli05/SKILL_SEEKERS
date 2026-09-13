export function FeatureExplanation({
  text,
  details,
}: {
  text: string;
  details?: string;
}) {
  return (
    <div className="mt-1 max-w-3xl">
      <p className="text-sm text-[var(--muted)]">{text}</p>
      {details ? (
        <details className="mt-1">
          <summary className="cursor-pointer text-sm text-[var(--navy)]">More details</summary>
          <p className="mt-1 text-sm text-[var(--muted)]">{details}</p>
        </details>
      ) : null}
    </div>
  );
}
