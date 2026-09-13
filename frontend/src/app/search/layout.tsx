import { Suspense, type ReactNode } from "react";

export default function SearchLayout({ children }: { children: ReactNode }) {
  return <Suspense fallback={<p className="text-sm text-[var(--muted)]">Loading search…</p>}>{children}</Suspense>;
}
