import { Suspense } from "react";

import { DemoCaseJourney } from "@/components/DemoCaseJourney";
import { PageState } from "@/components/ui/PageState";

export default function DemoCasePage() {
  return (
    <Suspense fallback={<PageState kind="loading" message="Loading demo case…" />}>
      <DemoCaseJourney />
    </Suspense>
  );
}
