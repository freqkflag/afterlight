"use client";

import { useEffect, useState } from "react";

interface Executor {
  id: string;
  executor_name: string;
  executor_email: string;
  relationship: string;
  access_level: string;
  status: string;
}

export default function ExecutorPage() {
  const [executors, setExecutors] = useState<Executor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchExecutors() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/executor", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error("Failed to load executors");
        const json = await res.json();
        setExecutors(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchExecutors();
  }, []);

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
        <h1 className="text-3xl font-bold text-amber-400">Executor Access</h1>
        <p className="mt-2 text-navy-300">
          Manage who can access your digital estate.
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-3">
          {executors.length === 0 ? (
            <p className="text-navy-400">No executors added yet.</p>
          ) : (
            executors.map((executor) => (
              <div
                key={executor.id}
                className="flex items-center justify-between rounded-lg bg-navy-900/50 p-4 border border-navy-800"
              >
                <div>
                  <p className="font-medium text-white">{executor.executor_name}</p>
                  <p className="text-sm text-navy-400">
                    {executor.relationship} · {executor.executor_email}
                  </p>
                </div>
                <div className="text-right">
                  <span className="rounded-full bg-navy-800 px-2 py-1 text-xs text-navy-300">
                    {executor.access_level}
                  </span>
                  <p className="mt-1 text-xs text-navy-500 capitalize">{executor.status}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
