"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

interface DashboardData {
  total_assets: number;
  total_vault_items: number;
  total_legacy_messages: number;
  total_estimated_value_cents: number;
  assets_by_kind: Record<string, number>;
  recent_activity: Array<{
    action: string;
    description: string;
    created_at: string;
  }>;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void api<DashboardData>("/executor/dashboard/summary")
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load"),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell
      title="Dashboard"
      subtitle="Your digital estate at a glance."
    >
      {loading ? <p className="text-navy-300">Loading…</p> : null}
      {error ? <p className="text-red-400">{error}</p> : null}

      {!loading && !error ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Assets" value={data?.total_assets ?? 0} />
            <StatCard label="Vault Items" value={data?.total_vault_items ?? 0} />
            <StatCard
              label="Legacy Messages"
              value={data?.total_legacy_messages ?? 0}
            />
            <StatCard
              label="Est. Value"
              value={`$${((data?.total_estimated_value_cents ?? 0) / 100).toLocaleString()}`}
            />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <QuickAction
              href="/vault"
              title="Manage Vault"
              description="Passwords, seed phrases, documents"
            />
            <QuickAction
              href="/assets"
              title="Digital Assets"
              description="Accounts, subscriptions, investments"
            />
            <QuickAction
              href="/dead-mans-switch"
              title="Dead Man's Switch"
              description="Check-in status and configuration"
            />
            <QuickAction
              href="/legacy-messages"
              title="Legacy Messages"
              description="Scheduled messages for loved ones"
            />
            <QuickAction
              href="/executor"
              title="Executors"
              description="Invite who can access your estate"
            />
            <QuickAction
              href="/executor/portal"
              title="Executor Portal"
              description="Checklists for estates you manage"
            />
          </div>

          {data?.recent_activity && data.recent_activity.length > 0 ? (
            <div className="mt-8">
              <h2 className="text-xl font-semibold text-navy-100">
                Recent Activity
              </h2>
              <div className="mt-4 space-y-2">
                {data.recent_activity.map((activity, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg border border-navy-800 bg-navy-900/50 p-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-navy-100">
                        {activity.description}
                      </p>
                      <p className="text-xs text-navy-400">
                        {new Date(activity.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className="rounded bg-navy-800 px-2 py-1 text-xs text-navy-300">
                      {activity.action}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </AppShell>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6">
      <p className="text-sm text-navy-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
    </div>
  );
}

function QuickAction({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-xl border border-navy-800 bg-navy-900/50 p-6 transition hover:border-amber-500/50"
    >
      <h3 className="font-semibold text-amber-400">{title}</h3>
      <p className="mt-1 text-sm text-navy-300">{description}</p>
    </Link>
  );
}
