"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Executor } from "@/types";

export default function ExecutorPage() {
  const [executors, setExecutors] = useState<Executor[]>([]);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [relationship, setRelationship] = useState("spouse");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setExecutors(await api<Executor[]>("/executor"));
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
      await api("/executor", {
        method: "POST",
        body: JSON.stringify({
          executor_name: name,
          executor_email: email,
          relationship,
          access_level: "full",
        }),
      });
      setName("");
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not invite executor");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell
      title="Executors"
      subtitle="Invite the people who should receive a checklist when it matters."
    >
      <p className="mb-6 text-sm text-navy-400">
        Invited executors sign in and open the{" "}
        <Link href="/executor/portal" className="text-amber-400 hover:underline">
          executor portal
        </Link>
        .
      </p>
      {error ? (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <form
        onSubmit={handleCreate}
        className="mb-10 grid gap-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6 sm:grid-cols-3"
      >
        <h2 className="sm:col-span-3 text-lg font-semibold text-white">
          Invite executor
        </h2>
        <input
          required
          placeholder="Full name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
        />
        <input
          required
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
        />
        <input
          required
          placeholder="Relationship"
          value={relationship}
          onChange={(e) => setRelationship(e.target.value)}
          className="rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
        />
        <div className="sm:col-span-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {saving ? "Sending…" : "Invite"}
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {executors.length === 0 ? (
          <p className="text-navy-400">No executors invited yet.</p>
        ) : (
          executors.map((ex) => (
            <div
              key={ex.id}
              className="rounded-lg border border-navy-800 bg-navy-900/50 p-4"
            >
              <p className="font-medium text-white">{ex.executor_name}</p>
              <p className="text-sm text-navy-400">
                {ex.executor_email} · {ex.relationship} · {ex.status}
              </p>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
