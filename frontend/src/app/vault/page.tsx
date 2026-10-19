"use client";

import { useEffect, useState } from "react";

interface VaultItem {
  id: string;
  kind: string;
  title_hint: string;
  created_at: string;
}

export default function VaultPage() {
  const [items, setItems] = useState<VaultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchVault() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/vault", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error("Failed to load vault");
        const json = await res.json();
        setItems(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchVault();
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
        <h1 className="text-3xl font-bold text-amber-400">Vault</h1>
        <p className="mt-2 text-navy-300">
          Your encrypted passwords, seed phrases, and documents.
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-3">
          {items.length === 0 ? (
            <p className="text-navy-400">No vault items yet.</p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-lg bg-navy-900/50 p-4 border border-navy-800"
              >
                <div>
                  <p className="font-medium text-white">{item.title_hint}</p>
                  <p className="text-sm text-navy-400">{item.kind}</p>
                </div>
                <p className="text-xs text-navy-500">
                  {new Date(item.created_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
