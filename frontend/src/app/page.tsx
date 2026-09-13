import { Suspense } from "react";

import { OfficerDashboard } from "@/components/OfficerDashboard";
import { PageState } from "@/components/ui/PageState";

export default function DashboardPage() {
  return (
    <Suspense fallback={<PageState kind="loading" message="Loading officer dashboard…" />}>
      <OfficerDashboard />
    </Suspense>
  );
}
