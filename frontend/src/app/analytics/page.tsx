"use client";

import { CapabilityHub } from "@/components/system/CapabilityHub";
import { ANALYTICS_MODULES, FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function AnalyticsCenterPage() {
  return (
    <CapabilityHub
      kicker="Analytics"
      title="ANALYTICS CENTER"
      explanation={FEATURE_EXPLANATIONS.analytics}
      items={ANALYTICS_MODULES}
    />
  );
}
