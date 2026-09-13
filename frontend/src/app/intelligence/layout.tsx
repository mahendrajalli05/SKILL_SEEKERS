import { Suspense, type ReactNode } from "react";

import { PageState } from "@/components/ui/PageState";

export default function HubLayout({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageState kind="loading" message="Loading…" />}>{children}</Suspense>;
}
