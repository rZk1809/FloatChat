import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Github, Code2, Zap, Shield, Globe } from "lucide-react";
import { REPO_URL } from "@/lib/constants";

export const metadata: Metadata = {
  title: "API Docs — FloatChat",
  description: "Documentation for the FloatChat REST API endpoints.",
};

interface Endpoint {
  method: "GET" | "POST";
  path: string;
  desc: string;
  request?: string;
  response: string;
  notes?: string;
}

const ENDPOINTS: Endpoint[] = [
  {
    method: "POST",
    path: "/api/chat",
    desc: "Send a message to the FloatChat AI assistant and receive a response.",
    request: JSON.stringify(
      { messages: [{ role: "user", content: "What is a T-S diagram?" }] },
      null,
      2
    ),
    response: JSON.stringify({ content: "A T-S diagram (Temperature-Salinity diagram)..." }, null, 2),
    notes: "Rate limited to 20 requests per minute per IP. Messages array limited to 20 entries, 4000 chars each.",
  },
  {
    method: "GET",
    path: "/api/health",
    desc: "Check the health and status of the FloatChat web service.",
    response: JSON.stringify(
      { status: "ok", version: "1.2.0", timestamp: "2025-08-14T00:00:00.000Z", services: { chat: true } },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/regions",
    desc: "Retrieve information about the ocean regions covered by the FloatChat dataset.",
    response: JSON.stringify(
      {
        regions: [
          { name: "Bay of Bengal", coords: "5-25°N, 80-100°E", profiles: 1842, avgSurfaceTemp: 28.4 },
        ],
        total: 4,
      },
      null,
      2
    ),
  },
  {
    method: "POST",
    path: "/api/suggestions",
    desc: "Get context-aware query suggestions based on the current conversation.",
    request: JSON.stringify({ context: "We were discussing thermocline depth" }, null, 2),
    response: JSON.stringify(
      { suggestions: ["What causes thermocline shoaling?", "How deep is the thermocline in summer?"] },
      null,
      2
    ),
  },
  {
    method: "POST",
    path: "/api/feedback",
    desc: "Submit a thumbs-up or thumbs-down rating for an AI response.",
    request: JSON.stringify({ rating: "up", messageIndex: 2, query: "What is a T-S diagram?" }, null, 2),
    response: JSON.stringify({ received: true, rating: "up", totals: { up: 5, down: 1 } }, null, 2),
  },
  {
    method: "POST",
    path: "/api/export",
    desc: "Export a conversation in Markdown, JSON, or plain text format.",
    request: JSON.stringify(
      { messages: [{ role: "user", content: "Hello", timestamp: 1723000000000 }], format: "markdown" },
      null,
      2
    ),
    response: "Returns a file download (Content-Disposition: attachment)",
    notes: "Supported formats: markdown, json, txt. Max 100 messages.",
  },
];

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  POST: "bg-blue-500/15 text-blue-400 border-blue-500/30",
};

export default function Docs() {
  return (
    <main className="min-h-screen bg-ocean-950">
      <nav className="fixed top-0 left-0 right-0 z-50 nav-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm">
            <ArrowLeft size={16} />
            Back
          </Link>
          <div className="h-4 w-px bg-slate-700" />
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg">🌊</span>
            <span className="font-bold text-white">Float<span className="gradient-text">Chat</span></span>
          </Link>
          <div className="ml-auto">
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-ocean-700 border border-cyan-500/20 text-sm text-slate-300 hover:text-white transition-all">
              <Github size={15} />
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 pt-32 pb-24">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs text-blue-400 mb-4">
            <Code2 size={12} />
            REST API
          </div>
          <h1 className="text-5xl font-black text-white mb-4">
            API <span className="gradient-text">Documentation</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            The FloatChat web service exposes REST endpoints for chat, data access, and conversation management.
          </p>
        </div>

        {/* Base URL */}
        <div className="glass rounded-xl p-5 border border-cyan-500/10 mb-8">
          <h2 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
            <Globe size={14} className="text-cyan-400" />
            Base URL
          </h2>
          <code className="text-sm text-cyan-300 font-mono bg-ocean-800/60 px-3 py-2 rounded-lg block">
            https://floatchat.vercel.app
          </code>
          <p className="text-xs text-slate-500 mt-2">All endpoints accept and return JSON unless otherwise noted. CORS is allowed for all origins.</p>
        </div>

        {/* Auth */}
        <div className="glass rounded-xl p-5 border border-cyan-500/10 mb-8">
          <h2 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
            <Shield size={14} className="text-cyan-400" />
            Authentication
          </h2>
          <p className="text-sm text-slate-400">
            The web API requires no authentication from clients. The <code className="text-cyan-300 text-xs">ANTHROPIC_API_KEY</code> is
            configured server-side. Rate limiting (20 req/min/IP) is enforced on the <code className="text-cyan-300 text-xs">/api/chat</code> endpoint.
          </p>
        </div>

        {/* Endpoints */}
        <div className="space-y-6">
          {ENDPOINTS.map((ep) => (
            <div key={ep.path} className="glass rounded-2xl border border-cyan-500/10 overflow-hidden">
              <div className="flex items-center gap-3 px-5 py-4 border-b border-cyan-500/10 bg-ocean-800/30">
                <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${METHOD_COLORS[ep.method]}`}>
                  {ep.method}
                </span>
                <code className="text-slate-200 font-mono text-sm">{ep.path}</code>
              </div>
              <div className="p-5">
                <p className="text-slate-300 text-sm mb-4">{ep.desc}</p>
                {ep.notes && (
                  <div className="flex gap-2 mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <Zap size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-300">{ep.notes}</p>
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ep.request && (
                    <div>
                      <p className="text-xs text-slate-500 mb-1.5 font-semibold uppercase tracking-wider">Request Body</p>
                      <pre className="text-xs text-cyan-300 font-mono bg-ocean-800/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap">
                        {ep.request}
                      </pre>
                    </div>
                  )}
                  <div className={ep.request ? "" : "md:col-span-2"}>
                    <p className="text-xs text-slate-500 mb-1.5 font-semibold uppercase tracking-wider">Response</p>
                    <pre className="text-xs text-emerald-300 font-mono bg-ocean-800/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap">
                      {ep.response}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center text-slate-500 text-sm">
          <p>For the full Python backend API (PostgreSQL + ChromaDB queries), see the</p>
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors">
            FloatChat GitHub repository
          </a>
        </div>
      </div>
    </main>
  );
}
