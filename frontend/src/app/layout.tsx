import type { ReactNode } from "react";

import { AppShell } from "@/components/AppShell";
import "./globals.css";

export const metadata = {
  title: "SARVSAKSHI",
  description:
    "MPLADS Project Integrity & Investigation Layer. AI recommends. Authorized officers decide.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
