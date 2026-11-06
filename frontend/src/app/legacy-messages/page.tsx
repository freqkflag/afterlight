"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { VaultUnlock } from "@/components/VaultUnlock";
import { api } from "@/lib/api";
import { encryptSecret, loadCachedDek } from "@/lib/crypto";
import type { LegacyMessage } from "@/types";

export default function LegacyMessagesPage() {
  const [dek, setDek] = useState<CryptoKey | null>(null);
  const [messages, setMessages] = useState<LegacyMessage[]>([]);
  const [error, setError] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [trigger, setTrigger] = useState("after_death");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setMessages(await api<LegacyMessage[]>("/legacy-messages"));
  }, []);

  useEffect(() => {
    void (async () => {
      const cached = await loadCachedDek();
      if (cached) setDek(cached);
    })();
  }, []);

  useEffect(() => {
    void load().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load"),
    );
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!dek) {
      setError("Unlock your vault first so message content can be encrypted.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const { encrypted_data, nonce } = await encryptSecret(dek, body);
      await api("/legacy-messages", {
        method: "POST",
        body: JSON.stringify({
          recipient_email: recipientEmail,
          recipient_name: recipientName,
          subject,
          encrypted_content: encrypted_data,
          nonce,
          trigger,
        }),
      });
      setRecipientName("");
      setRecipientEmail("");
      setSubject("");
      setBody("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create message");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell
      title="Legacy Messages"
      subtitle="Compose encrypted messages for delivery after release triggers."
    >
      {error ? (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      {!dek ? (
        <div className="mb-8">
          <VaultUnlock onUnlocked={setDek} />
        </div>
      ) : (
        <form
          onSubmit={handleCreate}
          className="mb-10 space-y-4 rounded-lg border border-navy-800 bg-navy-900/40 p-6"
        >
          <h2 className="text-lg font-semibold text-white">Compose message</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <input
              required
              placeholder="Recipient name"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              className="rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            />
            <input
              required
              type="email"
              placeholder="Recipient email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              className="rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            />
          </div>
          <input
            required
            placeholder="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
          <select
            value={trigger}
            onChange={(e) => setTrigger(e.target.value)}
            className="w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          >
            <option value="after_death">After death (switch release)</option>
            <option value="specific_date">Specific date</option>
            <option value="birthday">Milestone / birthday</option>
            <option value="anniversary">Anniversary</option>
          </select>
          <textarea
            required
            rows={4}
            placeholder="Message body (encrypted in your browser)"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
          />
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {saving ? "Encrypting…" : "Save message"}
          </button>
        </form>
      )}

      <div className="space-y-3">
        {messages.length === 0 ? (
          <p className="text-navy-400">No legacy messages yet.</p>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className="rounded-lg border border-navy-800 bg-navy-900/50 p-4"
            >
              <p className="font-medium text-white">{m.subject}</p>
              <p className="text-sm text-navy-400">
                To {m.recipient_name} ({m.recipient_email}) · {m.trigger} ·{" "}
                {m.status}
              </p>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
