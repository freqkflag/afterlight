"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(245,158,11,0.12),_transparent_55%),linear-gradient(180deg,#0a0820_0%,#0f0d2e_45%,#151238_100%)]" />
      <div className="relative mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-8 py-16">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-amber-500/80">
          Early access
        </p>
        <h1 className="mt-4 text-5xl font-bold tracking-tight text-amber-400 sm:text-6xl">
          Afterlight
        </h1>
        <p className="mt-4 text-xl text-navy-200">
          Your digital life, handled with care when you&apos;re gone.
        </p>
        <p className="mt-6 max-w-xl text-navy-300">
          Catalog your accounts, keep secrets in a client-encrypted vault, and
          prove you&apos;re alive with a dead man&apos;s switch — so the people
          you trust get a clear checklist when it matters.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/register"
            className="rounded-lg bg-amber-500 px-6 py-3 font-semibold text-navy-950 transition hover:bg-amber-400"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-navy-400 px-6 py-3 font-semibold text-navy-200 transition hover:bg-navy-800"
          >
            Sign In
          </Link>
          <Link
            href="/executor/portal"
            className="rounded-lg px-6 py-3 font-semibold text-amber-400/90 transition hover:text-amber-300"
          >
            Executor portal
          </Link>
        </div>
      </div>
    </main>
  );
}
