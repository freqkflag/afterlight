"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

interface SwitchStatus {
  status: string;
  last_check_in_at?: string | null;
  next_check_in_due_at?: string | null;
  check_in_interval_days?: number;
  grace_period_days?: number;
  missed_checkins_before_escalation?: number;
  trusted_contacts?: Array<{
    name: string;
    email: string;
    relationship: string;
    notified_of_death?: boolean;
  }>;
}

interface Contact {
  id: string;
  name: string;
  email: string;
  relationship: string;
  priority: number;
}

export default function DeadMansSwitchPage() {
  const [status, setStatus] = useState<SwitchStatus | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState("");
  const [intervalDays, setIntervalDays] = useState(30);
  const [graceDays, setGraceDays] = useState(14);
  const [missed, setMissed] = useState(2);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [relationship, setRelationship] = useState("sibling");

  const load = useCallback(async () => {
    const s = await api<SwitchStatus>("/dead-mans-switch/status");
    setStatus(s);
    if (s.status !== "not_configured") {
      setIntervalDays(s.check_in_interval_days ?? 30);
      setGraceDays(s.grace_period_days ?? 14);
      setMissed(s.missed_checkins_before_escalation ?? 2);
    }
    setContacts(await api<Contact[]>("/dead-mans-switch/trusted-contacts"));
  }, []);

  useEffect(() => {
    void load().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load"),
    );
  }, [load]);

  async function configure(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/dead-mans-switch/configure", {
        method: "POST",
        body: JSON.stringify({
          check_in_interval_days: intervalDays,
          grace_period_days: graceDays,
          missed_checkins_before_escalation: missed,
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Configure failed");
    }
  }

  async function checkIn() {
    setError("");
    try {
      await api("/dead-mans-switch/check-in", {
        method: "POST",
        body: JSON.stringify({ method: "app" }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check-in failed");
    }
  }

  async function pauseOrResume() {
    const path =
      status?.status === "paused"
        ? "/dead-mans-switch/resume"
        : "/dead-mans-switch/pause";
    await api(path, { method: "POST" });
    await load();
  }

  async function addContact(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/dead-mans-switch/trusted-contacts", {
        method: "POST",
        body: JSON.stringify({ name, email, relationship, priority: 1 }),
      });
      setName("");
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add contact");
    }
  }

  return (
    <AppShell
      title="Dead Man's Switch"
      subtitle="Check in regularly. Conservatively escalate only after missed windows."
    >
      {error ? (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <div className="mb-8 rounded-lg border border-navy-800 bg-navy-900/40 p-6">
        <p className="text-sm text-navy-400">Status</p>
        <p className="mt-1 text-2xl font-semibold text-amber-400">
          {status?.status ?? "loading…"}
        </p>
        {status?.next_check_in_due_at ? (
          <p className="mt-2 text-sm text-navy-300">
            Next check-in due{" "}
            {new Date(status.next_check_in_due_at).toLocaleString()}
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void checkIn()}
            className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-navy-950 hover:bg-amber-400"
          >
            Check in now
          </button>
          {status && status.status !== "not_configured" ? (
            <button
              type="button"
              onClick={() => void pauseOrResume()}
              className="rounded-lg border border-navy-500 px-4 py-2 text-navy-200 hover:bg-navy-800"
            >
              {status.status === "paused" ? "Resume" : "Pause"}
            </button>
          ) : null}
        </div>
      </div>

      <form
        onSubmit={configure}
        className="mb-10 grid gap-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6 sm:grid-cols-3"
      >
        <h2 className="sm:col-span-3 text-lg font-semibold text-white">
          Configuration
        </h2>
        <div>
          <label className="block text-sm text-navy-200">
            Check-in interval (days)
          </label>
          <input
            type="number"
            min={7}
            max={365}
            value={intervalDays}
            onChange={(e) => setIntervalDays(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div>
          <label className="block text-sm text-navy-200">Grace period (days)</label>
          <input
            type="number"
            min={1}
            max={90}
            value={graceDays}
            onChange={(e) => setGraceDays(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div>
          <label className="block text-sm text-navy-200">
            Missed check-ins before escalation
          </label>
          <input
            type="number"
            min={1}
            max={10}
            value={missed}
            onChange={(e) => setMissed(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
        </div>
        <div className="sm:col-span-3">
          <button
            type="submit"
            className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400"
          >
            Save configuration
          </button>
        </div>
      </form>

      <form
        onSubmit={addContact}
        className="mb-8 grid gap-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6 sm:grid-cols-3"
      >
        <h2 className="sm:col-span-3 text-lg font-semibold text-white">
          Trusted contacts
        </h2>
        <input
          required
          placeholder="Name"
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
            className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400"
          >
            Add contact
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {contacts.length === 0 ? (
          <p className="text-navy-400">No trusted contacts yet.</p>
        ) : (
          contacts.map((c) => (
            <div
              key={c.id}
              className="rounded-lg border border-navy-800 bg-navy-900/50 p-4"
            >
              <p className="font-medium text-white">{c.name}</p>
              <p className="text-sm text-navy-400">
                {c.email} · {c.relationship}
              </p>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
