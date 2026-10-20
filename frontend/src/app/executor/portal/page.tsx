"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, getAccessToken } from "@/lib/api";
import type { EstateDetail, EstateSummary } from "@/types";

export default function ExecutorPortalPage() {
  const [estates, setEstates] = useState<EstateSummary[]>([]);
  const [selected, setSelected] = useState<EstateDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      window.location.href = "/login?next=/executor/portal";
      return;
    }
    setEstates(await api<EstateSummary[]>("/executor/portal/estates"));
  }, []);

  useEffect(() => {
    void load()
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load estates"),
      )
      .finally(() => setLoading(false));
  }, [load]);

  async function accept(executorId: string) {
    setError("");
    try {
      await api("/executor/portal/accept", {
        method: "POST",
        body: JSON.stringify({ executor_id: executorId }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Accept failed");
    }
  }

  async function openEstate(grantorUserId: string) {
    setError("");
    try {
      const detail = await api<EstateDetail>(
        `/executor/portal/estates/${grantorUserId}`,
      );
      setSelected(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not open estate");
    }
  }

  return (
    <main className="min-h-screen bg-navy-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-widest text-amber-500/80">
              Executor portal
            </p>
            <h1 className="mt-2 text-3xl font-bold text-amber-400">
              Here&apos;s everything. Here&apos;s what to do.
            </h1>
            <p className="mt-2 text-navy-300">
              Accept invitations and follow the checklist for each estate.
            </p>
          </div>
          <Link href="/dashboard" className="text-sm text-navy-400 hover:text-white">
            Owner dashboard
          </Link>
        </div>

        {error ? (
          <div className="mb-4 rounded-lg border border-red-700 bg-red-900/30 p-3 text-sm text-red-300">
            {error}
          </div>
        ) : null}

        {loading ? (
          <p className="text-navy-300">Loading…</p>
        ) : estates.length === 0 ? (
          <p className="text-navy-400">
            No estate invitations for your account email yet.
          </p>
        ) : (
          <div className="space-y-4">
            {estates.map((estate) => (
              <div
                key={estate.grantor_user_id}
                className="rounded-lg border border-navy-800 bg-navy-900/50 p-5"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-white">
                      {estate.grantor_name}
                    </p>
                    <p className="text-sm text-navy-400">
                      {estate.grantor_email} · {estate.status} · switch:{" "}
                      {estate.switch_status ?? "none"}
                    </p>
                    <p className="mt-1 text-sm text-navy-300">
                      {estate.total_assets} assets · {estate.total_vault_items}{" "}
                      vault items · {estate.total_legacy_messages} messages
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {estate.status === "pending" ? (
                      <button
                        type="button"
                        onClick={() => void accept(estate.executor_id)}
                        className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-navy-950"
                      >
                        Accept invite
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => void openEstate(estate.grantor_user_id)}
                        className="rounded-lg border border-amber-500/60 px-4 py-2 text-sm text-amber-400"
                      >
                        Open checklist
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {selected ? (
          <section className="mt-10 rounded-lg border border-navy-700 bg-navy-900/60 p-6">
            <h2 className="text-2xl font-semibold text-amber-400">
              Checklist for {selected.grantor_name}
            </h2>
            <ol className="mt-6 space-y-3">
              {selected.checklist.map((step) => (
                <li
                  key={step.step}
                  className="rounded-lg border border-navy-800 bg-navy-950/50 p-4"
                >
                  <p className="font-medium text-white">
                    {step.step}. {step.title}{" "}
                    <span className="text-sm text-navy-400">
                      {step.done ? "✓" : "○"}
                    </span>
                  </p>
                  <p className="mt-1 text-sm text-navy-300">{step.detail}</p>
                </li>
              ))}
            </ol>

            <div className="mt-8 grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="font-semibold text-white">Assets</h3>
                <ul className="mt-2 space-y-1 text-sm text-navy-300">
                  {selected.assets.map((a) => (
                    <li key={a.id}>
                      {a.name} ({a.kind})
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-white">Vault titles</h3>
                <ul className="mt-2 space-y-1 text-sm text-navy-300">
                  {selected.vault_items.map((v) => (
                    <li key={v.id}>
                      {v.title_hint} ({v.kind})
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
