"use client";

import { DataModeBanner } from "@/components/DataModeBanner";
import { PageHeader } from "@/components/system/PageHeader";
import { HubTile } from "@/components/system/VisualKit";
import { parseDataMode, withModePath } from "@/lib/display";
import { useSearchParams } from "next/navigation";
import type { IconName } from "@/components/system/SvkIcon";

export function CapabilityHub({
  kicker,
  title,
  explanation,
  items,
}: {
  kicker: string;
  title: string;
  explanation: string;
  items: Array<{
    href: string;
    label: string;
    explanation: string;
    icon: IconName;
    tone?: "signal" | "violet" | "saffron" | "success" | "danger" | "indigo";
  }>;
}) {
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  return (
    <div className="space-y-6">
      <PageHeader kicker={kicker} title={title} explanation={explanation} />
      <DataModeBanner mode={mode} />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <HubTile
            key={item.href}
            href={withModePath(item.href, mode)}
            icon={item.icon}
            title={item.label}
            explanation={item.explanation}
            tone={item.tone}
          />
        ))}
      </div>
    </div>
  );
}
