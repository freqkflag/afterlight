"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Asset } from "@/types";

const KINDS = [
  "email",
  "banking",
  "investment",
  "crypto",
  "subscription",
  "social_media",
  "cloud_storage",
  "domain",
  "other",
];

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [kind, setKind] = useState("email");
  const [identifier, setIdentifier] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setAssets(await api<Asset[]>("/assets"));
  }, []);

  useEffect(() => {
    void load().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load"),
    );
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api("/assets", {
        method: "POST",
        body: JSON.stringify({
          kind,
          name,
          identifier: identifier || null,
          notes: notes || null,
        }),
      });
      setName("");
      setIdentifier("");
      setNotes("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create asset");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell
      title="Digital Assets"
      subtitle="Catalog accounts, subscriptions, and other digital property."
    >
      {error ? (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <form
        onSubmit={handleCreate}
        className="mb-10 grid gap-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6 sm:grid-cols-2"
      >
        <h2 className="sm:col-span-2 text-lg font-semibold text-white">
          Add asset
        </h2>
        <div>
          <label className="block text-sm text-navy-200">Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div>
          <label className="block text-sm text-navy-200">Kind</label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-navy-200">Identifier</label>
          <input
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="email or username"
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div>
          <label className="block text-sm text-navy-200">Notes</label>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Add asset"}
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {assets.length === 0 ? (
          <p className="text-navy-400">No assets yet.</p>
        ) : (
          assets.map((asset) => (
            <div
              key={asset.id}
              className="rounded-lg border border-navy-800 bg-navy-900/50 p-4"
            >
              <p className="font-medium text-white">{asset.name}</p>
              <p className="text-sm text-navy-400">
                {asset.kind}
                {asset.identifier ? ` · ${asset.identifier}` : ""}
              </p>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
