import { Suspense } from "react";

import { DemoCaseLaunch } from "@/components/DemoCaseLaunch";
import { PageState } from "@/components/ui/PageState";

export default function DemoCasesPage() {
  return (
    <Suspense fallback={<PageState kind="loading" message="Loading demo cases…" />}>
      <DemoCaseLaunch />
    </Suspense>
  );
}
