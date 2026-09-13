export function LoadingSkeleton({ lines = 3, label = "Loading" }: { lines?: number; label?: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-2">
      <p className="sr-only">{label}</p>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-3 bg-[var(--navy-soft)]"
          style={{ width: `${88 - index * 12}%` }}
        />
      ))}
    </div>
  );
}
