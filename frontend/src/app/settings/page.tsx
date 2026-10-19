"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");

    // In production: call API to change password
    setMessage("Password change functionality coming soon.");
  }

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold text-amber-400">Settings</h1>
        <p className="mt-2 text-navy-300">Manage your account and security.</p>

        <div className="mt-8 space-y-6">
          {/* Profile Section */}
          <div className="rounded-xl bg-navy-900/50 p-6 border border-navy-800">
            <h2 className="text-lg font-semibold text-white">Profile</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-navy-200">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Security Section */}
          <div className="rounded-xl bg-navy-900/50 p-6 border border-navy-800">
            <h2 className="text-lg font-semibold text-white">Security</h2>
            <form onSubmit={handlePasswordChange} className="mt-4 space-y-4">
              {message && (
                <div className="rounded-lg bg-green-900/30 border border-green-700 p-3 text-green-300 text-sm">
                  {message}
                </div>
              )}
              {error && (
                <div className="rounded-lg bg-red-900/30 border border-red-700 p-3 text-red-300 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-navy-200">
                  Current Password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-navy-200">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={14}
                  className="mt-1 w-full rounded-lg border border-navy-600 bg-navy-900 px-4 py-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                className="rounded-lg bg-amber-500 px-6 py-2.5 font-semibold text-navy-950 hover:bg-amber-400 transition"
              >
                Change Password
              </button>
            </form>
          </div>

          {/* Sign Out */}
          <div className="rounded-xl bg-navy-900/50 p-6 border border-navy-800">
            <button
              onClick={() => {
                localStorage.removeItem("access_token");
                window.location.href = "/login";
              }}
              className="rounded-lg border border-red-700 px-6 py-2.5 font-semibold text-red-300 hover:bg-red-900/30 transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
