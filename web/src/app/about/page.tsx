import type { Metadata } from "next";
import Link from "next/link";
import {
  Github,
  ArrowLeft,
  Database,
  Brain,
  Globe,
  Award,
  Code2,
  BookOpen,
  Layers,
  BarChart3,
} from "lucide-react";
import { REPO_URL, AUTHOR, OCEAN_REGIONS, DATASET_STATS } from "@/lib/constants";

export const metadata: Metadata = {
  title: "About — FloatChat",
  description:
    "Learn about the FloatChat team, mission, technology stack, and the ARGO oceanographic dataset powering the system.",
};

const TECH_STACK = [
  {
    category: "AI & LLMs",
    icon: Brain,
    color: "text-purple-400",
    items: [
      "Anthropic Claude (Haiku 4.5) — web demo assistant",
      "Ollama + qwen2:1.5b — local NL synthesis",
      "embeddinggemma:300m — profile embeddings",
    ],
  },
  {
    category: "Data & Storage",
    icon: Database,
    color: "text-blue-400",
    items: [
      "PostgreSQL + PostGIS — profiles & measurements",
      "ChromaDB — 4,922 vector embeddings",
      "ARGO Global Data Assembly Centre (GDAC)",
    ],
  },
  {
    category: "ML & Analysis",
    icon: BarChart3,
    color: "text-emerald-400",
    items: [
      "XGBoost — temperature prediction (R²=0.97)",
      "K-Means — 4-cluster water mass detection",
      "Isolation Forest — anomaly detection",
      "ARIMA/SARIMA — time-series modeling",
      "SHAP — explainability & feature importance",
    ],
  },
  {
    category: "Web & Infrastructure",
    icon: Layers,
    color: "text-cyan-400",
    items: [
      "Next.js 14 (App Router) + TypeScript",
      "Tailwind CSS + custom ocean theme",
      "Vercel — edge deployment",
      "Streamlit — local analysis UI",
      "FastAPI — Python REST backend",
    ],
  },
];

const DATA_SOURCES = [
  {
    name: "ARGO Global Data Assembly Centre",
    url: "https://www.argodatamgt.org/",
    desc: "Primary source of all 4,922 ARGO float profiles used in this analysis.",
  },
  {
    name: "International ARGO Program",
    url: "https://argo.ucsd.edu/",
    desc: "The global ocean observing network this project draws data from.",
  },
  {
    name: "GSW Oceanographic Toolbox",
    url: "https://teos-10.org/software.htm",
    desc: "Used for thermodynamic seawater property calculations.",
  },
];

export default function About() {
  return (
    <main className="min-h-screen bg-ocean-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 nav-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
          >
            <ArrowLeft size={16} />
            Back
          </Link>
          <div className="h-4 w-px bg-slate-700" />
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg">🌊</span>
            <span className="font-bold text-white">
              Float<span className="gradient-text">Chat</span>
            </span>
          </Link>
          <div className="ml-auto">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-ocean-700 border border-cyan-500/20 text-sm text-slate-300 hover:text-white transition-all duration-200"
            >
              <Github size={15} />
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 pt-32 pb-24">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-400 mb-4">
            <Award size={12} />
            SIH 2025 — Smart India Hackathon
          </div>
          <h1 className="text-5xl font-black text-white mb-4">
            About <span className="gradient-text">FloatChat</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
            An AI-powered oceanographic data analysis system built to make
            ARGO float data accessible through natural language.
          </p>
        </div>

        {/* Mission */}
        <section className="glass rounded-2xl p-8 border border-cyan-500/10 mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Globe size={18} className="text-cyan-400" />
            Mission
          </h2>
          <p className="text-slate-300 leading-relaxed mb-4">
            FloatChat was built for the{" "}
            <span className="text-cyan-300 font-medium">Smart India Hackathon 2025</span>{" "}
            to democratize access to ARGO oceanographic data. Today, extracting insights
            from the global ARGO dataset requires deep knowledge of Python, SQL,
            and oceanography. FloatChat removes that barrier — letting researchers,
            students, and policymakers ask questions in plain English and receive
            scientifically accurate answers with visualizations.
          </p>
          <p className="text-slate-400 leading-relaxed">
            The system focuses on the Indian Ocean basin — Bay of Bengal, Arabian Sea,
            and Southern Ocean — regions critical to Indian monsoon forecasting, maritime
            navigation, and climate science.
          </p>
        </section>

        {/* Author */}
        <section className="glass rounded-2xl p-8 border border-cyan-500/10 mb-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Code2 size={18} className="text-cyan-400" />
            Author
          </h2>
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xl flex-shrink-0">
              RK
            </div>
            <div>
              <h3 className="font-bold text-white text-lg">{AUTHOR}</h3>
              <p className="text-cyan-400 text-sm mb-3">RGK1809 · Full-Stack AI Developer</p>
              <p className="text-slate-400 text-sm leading-relaxed mb-4">
                Built the complete FloatChat system — multi-agent pipeline, PostgreSQL + ChromaDB
                hybrid retrieval, ML analytics suite, and Next.js web interface. Passionate about
                applying AI to climate and ocean science.
              </p>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
              >
                <Github size={14} />
                github.com/rZk1809
              </a>
            </div>
          </div>
        </section>

        {/* Dataset */}
        <section className="glass rounded-2xl p-8 border border-cyan-500/10 mb-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Database size={18} className="text-cyan-400" />
            Dataset
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: "ARGO Profiles", value: DATASET_STATS.totalProfiles.toLocaleString() },
              { label: "Ocean Regions", value: DATASET_STATS.totalRegions.toString() },
              { label: "Max Depth", value: `${DATASET_STATS.depthMax}m` },
              { label: "Date Range", value: `${DATASET_STATS.dateRange.start} – ${DATASET_STATS.dateRange.end}` },
            ].map(({ label, value }) => (
              <div key={label} className="text-center p-4 bg-ocean-800/50 rounded-xl">
                <div className="text-xl font-black gradient-text mb-1">{value}</div>
                <div className="text-xs text-slate-400">{label}</div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {OCEAN_REGIONS.map((r) => (
              <div key={r.name} className="flex gap-3 p-3 bg-ocean-800/30 rounded-lg">
                <div>
                  <p className="text-sm font-semibold text-white">{r.name}</p>
                  <p className="text-xs text-slate-500 font-mono">{r.coords}</p>
                  <p className="text-xs text-slate-400 mt-1">{r.profiles} profiles · avg {r.avgSurfaceTemp}°C</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Tech Stack */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Layers size={18} className="text-cyan-400" />
            Technology Stack
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {TECH_STACK.map(({ category, icon: Icon, color, items }) => (
              <div key={category} className="glass rounded-xl p-5 border border-cyan-500/10">
                <h3 className="font-semibold text-white mb-3 flex items-center gap-2 text-sm">
                  <Icon size={15} className={color} />
                  {category}
                </h3>
                <ul className="space-y-1.5">
                  {items.map((item) => (
                    <li key={item} className="text-xs text-slate-400 flex gap-1.5">
                      <span className="text-slate-600 flex-shrink-0 mt-0.5">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* Data Sources */}
        <section className="glass rounded-2xl p-8 border border-cyan-500/10 mb-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <BookOpen size={18} className="text-cyan-400" />
            Data Sources & Acknowledgments
          </h2>
          <div className="space-y-4">
            {DATA_SOURCES.map(({ name, desc }) => (
              <div key={name} className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 flex-shrink-0 mt-1.5" />
                <div>
                  <p className="text-sm font-semibold text-slate-200">{name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-6 pt-4 border-t border-slate-700/50">
            ARGO data is publicly available and collected by the international Argo Program,
            which is part of the Global Ocean Observing System.
          </p>
        </section>

        {/* License */}
        <div className="text-center text-slate-500 text-sm">
          <p>Released under the MIT License · © 2025 {AUTHOR}</p>
          <p className="mt-1">
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors">
              View source on GitHub
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}
