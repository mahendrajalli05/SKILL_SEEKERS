"use client";

import { CapabilityHub } from "@/components/system/CapabilityHub";
import { FEATURE_EXPLANATIONS, PLANNING_MODULES } from "@/lib/explanations";

export default function PlanningCenterPage() {
  return (
    <CapabilityHub
      kicker="Planning"
      title="PLANNING CENTER"
      explanation={FEATURE_EXPLANATIONS.planning}
      items={PLANNING_MODULES}
    />
  );
}
