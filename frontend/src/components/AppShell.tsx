import { Suspense, type ReactNode } from "react";

import { AppHeader } from "@/components/AppHeader";
import { CopilotDrawer } from "@/components/system/CopilotDrawer";
import { GovernanceStrip } from "@/components/system/GovernanceStrip";
import { PRODUCT_LAYER, PRODUCT_NAME } from "@/lib/explanations";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <Suspense
        fallback={
          <header className="bg-[var(--shell)] px-6 py-4 text-[var(--navy)]">
            <p className="svk-display text-xl font-semibold">{PRODUCT_NAME}</p>
            <p className="text-sm">{PRODUCT_LAYER}</p>
            <p className="mt-2 text-xs">Current Pilot: Andhra Pradesh</p>
          </header>
        }
      >
        <AppHeader />
      </Suspense>
      <main id="main-content" className="svk-shell-main mx-auto max-w-[92rem] px-4 py-6 lg:pl-[19.5rem] sm:px-6 sm:py-8">
        {children}
      </main>
      <footer className="border-t border-[var(--line)] px-6 py-4 text-center lg:pl-[19.5rem]">
        <p className="text-sm font-medium text-[var(--navy)]">
          {PRODUCT_NAME} · {PRODUCT_LAYER}
        </p>
        <p className="mt-1 text-xs text-[var(--muted)]">Current pilot: Andhra Pradesh</p>
        <GovernanceStrip />
      </footer>
      <Suspense fallback={null}>
        <CopilotDrawer />
      </Suspense>
    </div>
  );
}
