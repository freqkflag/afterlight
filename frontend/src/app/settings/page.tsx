"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, clearTokens } from "@/lib/api";
import { clearCachedDek } from "@/lib/crypto";

interface Me {
  email: string;
  full_name: string;
}

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void api<Me>("/auth/me")
      .then(setMe)
      .catch(() => setError("Could not load profile"));
  }, []);

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      await api("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      setMessage("Login password updated.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password change failed");
    }
  }

  function signOut() {
    clearCachedDek();
    clearTokens();
    window.location.href = "/login";
  }

  return (
    <AppShell title="Settings" subtitle="Manage your account and security.">
      <div className="max-w-2xl space-y-6">
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6">
          <h2 className="text-lg font-semibold text-white">Profile</h2>
          <p className="mt-3 text-navy-200">{me?.full_name ?? "…"}</p>
          <p className="text-sm text-navy-400">{me?.email ?? ""}</p>
          <p className="mt-4 text-sm text-navy-500">
            Vault master password is managed on the Vault page and never sent to
            the server.
          </p>
        </div>

        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6">
          <h2 className="text-lg font-semibold text-white">
            Change login password
          </h2>
          <form onSubmit={handlePasswordChange} className="mt-4 space-y-4">
            {message ? (
              <div className="rounded-lg border border-green-700 bg-green-900/30 p-3 text-sm text-green-300">
                {message}
              </div>
            ) : null}
            {error ? (
              <div className="rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
                {error}
              </div>
            ) : null}
            <input
              type="password"
              required
              placeholder="Current password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            />
            <input
              type="password"
              required
              minLength={14}
              placeholder="New password (14+ characters)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5"
            />
            <button
              type="submit"
              className="rounded-lg bg-amber-500 px-6 py-2.5 font-semibold text-navy-950 hover:bg-amber-400"
            >
              Update password
            </button>
          </form>
        </div>

        <button
          type="button"
          onClick={signOut}
          className="rounded-lg border border-red-700 px-6 py-2.5 font-semibold text-red-300 hover:bg-red-900/30"
        >
          Sign Out
        </button>
      </div>
    </AppShell>
  );
}
