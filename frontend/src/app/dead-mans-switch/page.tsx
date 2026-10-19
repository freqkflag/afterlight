"use client";

import { useEffect, useState } from "react";

interface SwitchStatus {
  status: string;
  last_check_in_at: string | null;
  next_check_in_due_at: string | null;
  check_in_interval_days: number;
  grace_period_days: number;
  trusted_contacts: Array<{
    name: string;
    email: string;
    relationship: string;
    has_confirmed_alive: boolean | null;
  }>;
}

export default function DeadMansSwitchPage() {
  const [status, setStatus] = useState<SwitchStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkingIn, setCheckingIn] = useState(false);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/dead-mans-switch/status", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error("Failed to load status");
        const json = await res.json();
        setStatus(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
  }, []);

  async function handleCheckIn() {
    setCheckingIn(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/dead-mans-switch/check-in", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ method: "app" }),
      });

      if (!res.ok) throw new Error("Check-in failed");
      const json = await res.json();
      // Refresh status
      const statusRes = await fetch("/api/dead-mans-switch/status", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const statusJson = await statusRes.json();
      setStatus(statusJson);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check-in failed");
    } finally {
      setCheckingIn(false);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-navy-300">Loading...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold text-amber-400">Dead Man&apos;s Switch</h1>
        <p className="mt-2 text-navy-300">
          Your proof-of-life check-in system.
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        {status && (
          <div className="mt-8 space-y-6">
            {/* Status Card */}
            <div className="rounded-xl bg-navy-900/50 p-6 border border-navy-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-navy-400">Status</p>
                  <p className="text-2xl font-bold text-white capitalize">
                    {status.status.replace(/_/g, " ")}
                  </p>
                </div>
                <button
                  onClick={handleCheckIn}
                  disabled={checkingIn}
                  className="rounded-lg bg-amber-500 px-6 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 transition disabled:opacity-50"
                >
                  {checkingIn ? "Checking in..." : "Check In Now"}
                </button>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-navy-400">Last Check-in</p>
                  <p className="text-white">
                    {status.last_check_in_at
                      ? new Date(status.last_check_in_at).toLocaleString()
                      : "Never"}
                  </p>
                </div>
                <div>
                  <p className="text-navy-400">Next Due</p>
                  <p className="text-white">
                    {status.next_check_in_due_at
                      ? new Date(status.next_check_in_due_at).toLocaleString()
                      : "Not scheduled"}
                  </p>
                </div>
                <div>
                  <p className="text-navy-400">Check-in Interval</p>
                  <p className="text-white">Every {status.check_in_interval_days} days</p>
                </div>
                <div>
                  <p className="text-navy-400">Grace Period</p>
                  <p className="text-white">{status.grace_period_days} days</p>
                </div>
              </div>
            </div>

            {/* Trusted Contacts */}
            {status.trusted_contacts.length > 0 && (
              <div className="rounded-xl bg-navy-900/50 p-6 border border-navy-800">
                <h2 className="text-lg font-semibold text-white">Trusted Contacts</h2>
                <div className="mt-4 space-y-3">
                  {status.trusted_contacts.map((contact, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-white">{contact.name}</p>
                        <p className="text-sm text-navy-400">
                          {contact.relationship} · {contact.email}
                        </p>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${
                          contact.has_confirmed_alive
                            ? "bg-green-900/50 text-green-300"
                            : "bg-navy-800 text-navy-300"
                        }`}
                      >
                        {contact.has_confirmed_alive ? "Confirmed alive" : "Pending"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
