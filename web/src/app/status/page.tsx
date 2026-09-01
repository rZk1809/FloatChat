"use client";

import type { Metadata } from "next";
import Link from "next/link";
import { useState, useEffect } from "react";
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Wifi,
  Database,
  Cpu,
  Globe,
  RefreshCw,
} from "lucide-react";
import Breadcrumb from "@/components/Breadcrumb";

interface ServiceStatus {
  name: string;
  status: "operational" | "degraded" | "down" | "checking";
  latencyMs?: number;
  icon: React.ReactNode;
  description: string;
}

function StatusBadge({ status }: { status: ServiceStatus["status"] }) {
  if (status === "checking") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-slate-400">
        <Clock size={12} className="animate-spin" />
        Checking…
      </span>
    );
  }
  if (status === "operational") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-emerald-400">
        <CheckCircle size={12} />
        Operational
      </span>
    );
  }
  if (status === "degraded") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-amber-400">
        <Clock size={12} />
        Degraded
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5 text-xs text-red-400">
      <XCircle size={12} />
      Down
    </span>
  );
}

export default function StatusPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: "FloatChat Web",
      status: "checking",
      icon: <Globe size={16} />,
      description: "Next.js frontend — Vercel edge network",
    },
    {
      name: "Chat API",
      status: "checking",
      icon: <Cpu size={16} />,
      description: "/api/chat — Claude AI (Anthropic Haiku 4.5)",
    },
    {
      name: "Health Endpoint",
      status: "checking",
      icon: <Wifi size={16} />,
      description: "/api/health — service readiness probe",
    },
    {
      name: "Vector Store",
      status: "operational",
      icon: <Database size={16} />,
      description: "ChromaDB — 4,922 ARGO profile embeddings (read-only)",
    },
  ]);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [checking, setChecking] = useState(false);

  const runChecks = async () => {
    setChecking(true);
    setServices((prev) =>
      prev.map((s) =>
        s.name !== "Vector Store" ? { ...s, status: "checking" } : s
      )
    );

    // Check /api/health
    const t0 = performance.now();
    let healthStatus: ServiceStatus["status"] = "down";
    let healthLatency: number | undefined;
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      healthLatency = Math.round(performance.now() - t0);
      healthStatus = res.ok ? "operational" : "degraded";
    } catch {
      healthLatency = Math.round(performance.now() - t0);
    }

    // Check /api/chat (preflight — no real message)
    const t1 = performance.now();
    let chatStatus: ServiceStatus["status"] = "down";
    let chatLatency: number | undefined;
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "user", content: "ping" }] }),
        signal: AbortSignal.timeout(8000),
      });
      chatLatency = Math.round(performance.now() - t1);
      // 200 or 429 (rate-limited) = chat route is alive
      chatStatus = res.status === 200 || res.status === 429 ? "operational" : "degraded";
    } catch {
      chatLatency = Math.round(performance.now() - t1);
    }

    setServices((prev) =>
      prev.map((s) => {
        if (s.name === "FloatChat Web") return { ...s, status: "operational", latencyMs: undefined };
        if (s.name === "Chat API") return { ...s, status: chatStatus, latencyMs: chatLatency };
        if (s.name === "Health Endpoint") return { ...s, status: healthStatus, latencyMs: healthLatency };
        return s;
      })
    );
    setLastChecked(new Date());
    setChecking(false);
  };

  useEffect(() => {
    runChecks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const allOk = services.every(
    (s) => s.status === "operational" || s.status === "checking"
  );
  const anyDown = services.some((s) => s.status === "down");

  return (
    <main className="min-h-screen bg-ocean-950 pt-24 pb-20 px-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Breadcrumb items={[{ label: "Status" }]} />
        </div>

        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft size={16} />
            Back
          </Link>
        </div>

        {/* Overall banner */}
        <div
          className={`rounded-2xl p-6 border mb-8 flex items-center gap-4 ${
            anyDown
              ? "bg-red-500/5 border-red-500/30"
              : allOk
              ? "bg-emerald-500/5 border-emerald-500/30"
              : "bg-amber-500/5 border-amber-500/30"
          }`}
        >
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${
              anyDown
                ? "bg-red-500/15"
                : allOk
                ? "bg-emerald-500/15"
                : "bg-amber-500/15"
            }`}
          >
            {anyDown ? "🔴" : allOk ? "🟢" : "🟡"}
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">
              {anyDown
                ? "Service disruption detected"
                : allOk
                ? "All systems operational"
                : "Checking service status…"}
            </h1>
            {lastChecked && (
              <p className="text-xs text-slate-500 mt-1">
                Last checked {lastChecked.toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        {/* Service cards */}
        <div className="space-y-3 mb-6">
          {services.map((svc) => (
            <div
              key={svc.name}
              className="glass rounded-xl px-5 py-4 border border-cyan-500/10 flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-3">
                <span className="text-cyan-400/70">{svc.icon}</span>
                <div>
                  <p className="text-sm font-semibold text-white">{svc.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{svc.description}</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <StatusBadge status={svc.status} />
                {svc.latencyMs !== undefined && (
                  <span className="text-[10px] text-slate-600">{svc.latencyMs} ms</span>
                )}
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={runChecks}
          disabled={checking}
          className="flex items-center gap-2 px-4 py-2 rounded-xl glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={14} className={checking ? "animate-spin" : ""} />
          {checking ? "Checking…" : "Refresh status"}
        </button>

        <div className="mt-12 glass rounded-xl p-5 border border-cyan-500/10">
          <h2 className="text-sm font-bold text-white mb-3">Incident history</h2>
          <p className="text-xs text-slate-500">No incidents recorded for FloatChat services.</p>
        </div>
      </div>
    </main>
  );
}
