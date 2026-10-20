"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { VaultUnlock } from "@/components/VaultUnlock";
import { api } from "@/lib/api";
import {
  decryptSecret,
  encryptSecret,
  loadCachedDek,
} from "@/lib/crypto";
import type { VaultItem, VaultItemKind } from "@/types";

const KINDS: VaultItemKind[] = [
  "password",
  "seed_phrase",
  "note",
  "api_key",
  "crypto_wallet",
  "document",
  "custom",
];

export default function VaultPage() {
  const [dek, setDek] = useState<CryptoKey | null>(null);
  const [items, setItems] = useState<VaultItem[]>([]);
  const [error, setError] = useState("");
  const [kind, setKind] = useState<VaultItemKind>("note");
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const loadItems = useCallback(async () => {
    const data = await api<VaultItem[]>("/vault");
    setItems(data);
  }, []);

  useEffect(() => {
    void (async () => {
      const cached = await loadCachedDek();
      if (cached) setDek(cached);
    })();
  }, []);

  useEffect(() => {
    if (!dek) return;
    void loadItems().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load vault"),
    );
  }, [dek, loadItems]);

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!dek) return;
    setSaving(true);
    setError("");
    const form = new FormData(e.currentTarget);
    const title = String(form.get("title_hint") || "");
    const secret = String(form.get("secret") || "");
    try {
      const { encrypted_data, nonce } = await encryptSecret(dek, secret);
      await api("/vault", {
        method: "POST",
        body: JSON.stringify({
          kind,
          title_hint: title,
          encrypted_data,
          nonce,
        }),
      });
      e.currentTarget.reset();
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save item");
    } finally {
      setSaving(false);
    }
  }

  async function reveal(item: VaultItem) {
    if (!dek) return;
    try {
      const plain = await decryptSecret(dek, item.encrypted_data, item.nonce);
      setRevealed((prev) => ({ ...prev, [item.id]: plain }));
    } catch {
      setError("Could not decrypt item. Is the vault unlocked with the correct key?");
    }
  }

  if (!dek) {
    return (
      <AppShell
        title="Vault"
        subtitle="Unlock with your master password to add or read secrets."
      >
        <VaultUnlock onUnlocked={setDek} />
      </AppShell>
    );
  }

  return (
    <AppShell
      title="Vault"
      subtitle="Secrets are encrypted in your browser before they reach the server."
    >
      {error ? (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <form
        onSubmit={handleCreate}
        className="mb-10 space-y-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6"
      >
        <h2 className="text-lg font-semibold text-white">Add vault item</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm text-navy-200">Title hint</label>
            <input
              required
              name="title_hint"
              className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
              placeholder="Chase Bank"
            />
          </div>
          <div>
            <label className="block text-sm text-navy-200">Kind</label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as VaultItemKind)}
              className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            >
              {KINDS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm text-navy-200">Secret</label>
          <textarea
            required
            name="secret"
            rows={3}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            placeholder="Password, seed phrase, or note"
          />
        </div>
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 disabled:opacity-50"
        >
          {saving ? "Encrypting…" : "Save encrypted"}
        </button>
      </form>

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="text-navy-400">No vault items yet.</p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="rounded-lg border border-navy-800 bg-navy-900/50 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-white">{item.title_hint}</p>
                  <p className="text-sm text-navy-400">{item.kind}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void reveal(item)}
                  className="text-sm text-amber-400 hover:text-amber-300"
                >
                  Reveal
                </button>
              </div>
              {revealed[item.id] ? (
                <pre className="mt-3 whitespace-pre-wrap rounded bg-navy-950 p-3 text-sm text-navy-200">
                  {revealed[item.id]}
                </pre>
              ) : null}
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
