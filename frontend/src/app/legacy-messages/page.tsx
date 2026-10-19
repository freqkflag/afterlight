"use client";

import { useEffect, useState } from "react";

interface LegacyMessage {
  id: string;
  recipient_name: string;
  recipient_email: string;
  subject: string;
  trigger: string;
  status: string;
  created_at: string;
}

export default function LegacyMessagesPage() {
  const [messages, setMessages] = useState<LegacyMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMessages() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch("/api/legacy-messages", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error("Failed to load messages");
        const json = await res.json();
        setMessages(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchMessages();
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
        <h1 className="text-3xl font-bold text-amber-400">Legacy Messages</h1>
        <p className="mt-2 text-navy-300">
          Messages for your loved ones, delivered when the time is right.
        </p>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-3">
          {messages.length === 0 ? (
            <p className="text-navy-400">No legacy messages yet.</p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className="flex items-center justify-between rounded-lg bg-navy-900/50 p-4 border border-navy-800"
              >
                <div>
                  <p className="font-medium text-white">{msg.subject}</p>
                  <p className="text-sm text-navy-400">
                    To: {msg.recipient_name} ({msg.recipient_email})
                  </p>
                </div>
                <div className="text-right">
                  <span className="rounded-full bg-navy-800 px-2 py-1 text-xs text-navy-300">
                    {msg.trigger}
                  </span>
                  <p className="mt-1 text-xs text-navy-500 capitalize">{msg.status}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
