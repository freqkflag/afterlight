"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearTokens } from "@/lib/api";
import { clearCachedDek } from "@/lib/crypto";
import { clsx } from "clsx";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/vault", label: "Vault" },
  { href: "/assets", label: "Assets" },
  { href: "/dead-mans-switch", label: "Dead Man's Switch" },
  { href: "/legacy-messages", label: "Legacy Messages" },
  { href: "/executor", label: "Executors" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}) {
  const pathname = usePathname();

  function signOut() {
    clearCachedDek();
    clearTokens();
    window.location.href = "/login";
  }

  return (
    <div className="min-h-screen bg-navy-950 text-white">
      <header className="border-b border-navy-800 bg-navy-950/90">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <Link href="/dashboard" className="text-lg font-bold text-amber-400">
            Afterlight
          </Link>
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "rounded-md px-3 py-1.5 transition",
                  pathname === item.href
                    ? "bg-navy-800 text-amber-400"
                    : "text-navy-300 hover:bg-navy-900 hover:text-white",
                )}
              >
                {item.label}
              </Link>
            ))}
            <button
              type="button"
              onClick={signOut}
              className="rounded-md px-3 py-1.5 text-navy-400 hover:text-white"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <h1 className="text-3xl font-bold text-amber-400">{title}</h1>
        {subtitle ? <p className="mt-2 text-navy-300">{subtitle}</p> : null}
        <div className="mt-8">{children}</div>
      </main>
    </div>
  );
}
