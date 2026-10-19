"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold tracking-tight text-amber-400">
          Afterlight
        </h1>
        <p className="mt-4 text-xl text-navy-200">
          Your digital life, handled with care when you&apos;re gone.
        </p>
        <p className="mt-6 text-navy-300">
          Afterlight is the executor-grade platform for digital estate planning.
          Encrypted vault, dead man&apos;s switch, legacy messages, and a clean
          dashboard for the people you trust.
        </p>
        <div className="mt-10 flex gap-4 justify-center">
          <Link
            href="/login"
            className="rounded-lg bg-amber-500 px-6 py-3 font-semibold text-navy-950 hover:bg-amber-400 transition"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="rounded-lg border border-navy-400 px-6 py-3 font-semibold text-navy-200 hover:bg-navy-800 transition"
          >
            Get Started
          </Link>
        </div>
      </div>
    </main>
  );
}
