"use client";

import { useEffect, useState } from "react";

interface Asset {
  id: string;
  kind: string;
  name: string;
  identifier: string | null;
  status: string;
  estimated_value_cents: number | null;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchAssets() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/assets", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error("Failed to load assets");
        const json = await res.json();
        setAssets(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchAssets();
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
        <h1 className="text-3xl font-bold text-amber-400">Digital Assets</h1>
        <p className="mt-2 text-navy-300">
          Your accounts, subscriptions, and digital valuables.
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-3">
          {assets.length === 0 ? (
            <p className="text-navy-400">No assets yet.</p>
          ) : (
            assets.map((asset) => (
              <div
                key={asset.id}
                className="flex items-center justify-between rounded-lg bg-navy-900/50 p-4 border border-navy-800"
              >
                <div>
                  <p className="font-medium text-white">{asset.name}</p>
                  <p className="text-sm text-navy-400">
                    {asset.kind} {asset.identifier && `· ${asset.identifier}`}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-white">
                    {asset.estimated_value_cents
                      ? `$${(asset.estimated_value_cents / 100).toLocaleString()}`
                      : "—"}
                  </p>
                  <p className="text-xs text-navy-500 capitalize">{asset.status}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
