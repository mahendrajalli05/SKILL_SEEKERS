"use client";

import { CapabilityHub } from "@/components/system/CapabilityHub";
import { FEATURE_EXPLANATIONS, VERIFICATION_MODULES } from "@/lib/explanations";

export default function VerificationCenterPage() {
  return (
    <CapabilityHub
      kicker="Verification"
      title="VERIFICATION CENTER"
      explanation={FEATURE_EXPLANATIONS.verification}
      items={VERIFICATION_MODULES}
    />
  );
}
