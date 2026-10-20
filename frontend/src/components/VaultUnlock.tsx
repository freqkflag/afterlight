"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  cacheDek,
  createKeyBundle,
  unlockDek,
} from "@/lib/crypto";
import type { KeyBundleResponse } from "@/types";

export function VaultUnlock({
  onUnlocked,
}: {
  onUnlocked: (dek: CryptoKey) => void;
}) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"loading" | "unlock" | "setup">("loading");
  const [salt, setSalt] = useState("");
  const [bundle, setBundle] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const data = await api<KeyBundleResponse>("/auth/key-bundle");
        setSalt(data.encryption_salt);
        setBundle(data.encrypted_key_bundle);
        setMode(data.has_vault_key ? "unlock" : "setup");
      } catch {
        setError("Could not load vault key status.");
        setMode("unlock");
      }
    })();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "setup") {
        if (password.length < 12) {
          setError("Master password must be at least 12 characters.");
          return;
        }
        if (password !== confirm) {
          setError("Passwords do not match.");
          return;
        }
        const { bundleJson, dek } = await createKeyBundle(password, salt);
        await api("/auth/key-bundle", {
          method: "PUT",
          body: JSON.stringify({ encrypted_key_bundle: bundleJson }),
        });
        await cacheDek(dek);
        onUnlocked(dek);
        return;
      }

      if (!bundle) {
        setError("No vault key found. Set one up first.");
        setMode("setup");
        return;
      }
      const dek = await unlockDek(password, salt, bundle);
      await cacheDek(dek);
      onUnlocked(dek);
    } catch {
      setError(
        mode === "setup"
          ? "Could not create vault key."
          : "Wrong master password or corrupt key bundle.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (mode === "loading") {
    return <p className="text-navy-300">Loading vault…</p>;
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md space-y-4 rounded-lg border border-navy-800 bg-navy-900/50 p-6"
    >
      <h2 className="text-xl font-semibold text-white">
        {mode === "setup" ? "Create vault master password" : "Unlock vault"}
      </h2>
      <p className="text-sm text-navy-400">
        This password never leaves your browser. It is separate from your login
        password. If you lose it, vault contents cannot be recovered.
      </p>
      {error ? (
        <div className="rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}
      <div>
        <label className="block text-sm text-navy-200">Master password</label>
        <input
          type="password"
          required
          minLength={12}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5 text-white"
        />
      </div>
      {mode === "setup" ? (
        <div>
          <label className="block text-sm text-navy-200">Confirm</label>
          <input
            type="password"
            required
            minLength={12}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5 text-white"
          />
        </div>
      ) : null}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-amber-500 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 disabled:opacity-50"
      >
        {loading
          ? "Working…"
          : mode === "setup"
            ? "Create vault key"
            : "Unlock"}
      </button>
    </form>
  );
}
