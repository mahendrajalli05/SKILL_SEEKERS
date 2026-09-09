import Link from "next/link";
import type { ReactNode } from "react";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/search", label: "Search" },
  { href: "/need-impact", label: "Need & Impact" },
  { href: "/reviews", label: "Reviews" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="bg-[var(--navy)] text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[var(--saffron)]">
              SIH26102 · MoSPI
            </p>
            <Link href="/" className="text-xl font-semibold tracking-wide">
              SARVSAKSHI
            </Link>
            <p className="text-sm text-white/80">
              MPLADS Project Integrity & Investigation Layer
            </p>
          </div>
          <Link
            href="/login"
            className="border border-white/30 px-3 py-1.5 text-sm hover:bg-white/10"
          >
            Officer login
          </Link>
        </div>
        <nav className="bg-[var(--navy-mid)]">
          <div className="mx-auto flex max-w-6xl gap-6 px-6 py-2 text-sm">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href} className="hover:text-[var(--saffron)]">
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      <footer className="border-t border-[var(--line)] px-6 py-4 text-center text-sm text-[var(--muted)]">
        AI recommends. Authorized officers decide. Investigation priority and
        evidence confidence — not a legal finding of fraud.
      </footer>
    </div>
  );
}
