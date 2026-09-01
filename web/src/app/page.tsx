import Link from "next/link";
import {
  Github,
  ExternalLink,
  Database,
  Brain,
  BarChart3,
  Search,
  Layers,
  Zap,
  Map,
  Activity,
  ChevronDown,
  ArrowRight,
  Globe,
  TrendingUp,
  Shield,
  HelpCircle,
  BookOpen,
  Info,
} from "lucide-react";
import ChatDemo from "@/components/ChatDemo";
import GallerySection from "@/components/GallerySection";
import MobileNav from "@/components/MobileNav";
import AnimatedCounter from "@/components/AnimatedCounter";

const PLOTS = [
  { file: "ts_diagram_clusters.png", title: "T-S Diagram with Clusters", category: "Clustering" },
  { file: "map_clusters.png", title: "Geographic Cluster Distribution", category: "Clustering" },
  { file: "cluster_sizes.png", title: "Cluster Sizes", category: "Clustering" },
  { file: "clustering_metrics.png", title: "Clustering Metrics", category: "Clustering" },
  { file: "elbow_method.png", title: "Elbow Method (Optimal k)", category: "Clustering" },
  { file: "pairplot_clusters.png", title: "Feature Pairplot by Cluster", category: "Clustering" },
  { file: "temp_histograms_per_cluster.png", title: "Temperature Distributions", category: "Analysis" },
  { file: "salinity_histograms_per_cluster.png", title: "Salinity Distributions", category: "Analysis" },
  { file: "feature_importance.png", title: "XGBoost Feature Importance", category: "ML" },
  { file: "predicted_vs_actual_scatter.png", title: "Predicted vs Actual (Scatter)", category: "ML" },
  { file: "predicted_vs_actual_hexbin.png", title: "Predicted vs Actual (Hexbin)", category: "ML" },
  { file: "residuals_histogram.png", title: "Residuals Distribution", category: "ML" },
  { file: "residuals_qq_plot.png", title: "Residuals Q-Q Plot", category: "ML" },
  { file: "residuals_vs_actual.png", title: "Residuals vs Actual", category: "ML" },
  { file: "residuals_vs_predicted.png", title: "Residuals vs Predicted", category: "ML" },
  { file: "pdp_latitude.png", title: "Partial Dependence: Latitude", category: "XAI" },
  { file: "pdp_day_sin.png", title: "Partial Dependence: Day (sin)", category: "XAI" },
];

const FEATURES = [
  {
    icon: Brain,
    title: "Multi-Agent AI Pipeline",
    description: "4 specialized agents — Planner, Executor, Synthesizer, and Plotting — work in sequence to process natural language queries end-to-end.",
    color: "from-purple-500 to-blue-600",
    badge: "Core",
  },
  {
    icon: Search,
    title: "Hybrid RAG Retrieval",
    description: "ChromaDB semantic search over 4,922 ARGO profile embeddings combined with PostgreSQL structured queries for precise, context-aware answers.",
    color: "from-cyan-500 to-teal-600",
    badge: "RAG",
  },
  {
    icon: BarChart3,
    title: "Smart Visualization",
    description: "Automatically detects query intent to generate the right plot — T-S diagrams, depth profiles, geographic maps, and time series.",
    color: "from-emerald-500 to-cyan-600",
    badge: "Auto",
  },
  {
    icon: Layers,
    title: "ML Analytics Suite",
    description: "K-means clustering (k=4), XGBoost temperature prediction, Isolation Forest anomaly detection, and ARIMA/SARIMA time series modeling.",
    color: "from-orange-500 to-red-600",
    badge: "ML",
  },
  {
    icon: Shield,
    title: "Explainable AI (XAI)",
    description: "SHAP values, partial dependence plots, and structured audit logs give full transparency into every analysis decision made by the system.",
    color: "from-pink-500 to-rose-600",
    badge: "XAI",
  },
  {
    icon: Globe,
    title: "Indian Ocean Coverage",
    description: "Deep coverage of Bay of Bengal, Arabian Sea, broader Indian Ocean, and Southern Ocean — the strategic ocean regions for India.",
    color: "from-blue-500 to-indigo-600",
    badge: "Data",
  },
];

const STATS = [
  { value: 4922, label: "ARGO Profiles", icon: Database },
  { value: 4, label: "Ocean Regions", icon: Map },
  { value: 4, label: "AI Agents", icon: Brain },
  { value: 17, label: "Visualizations", icon: BarChart3 },
];

const ARCH_STEPS = [
  {
    step: "01",
    name: "Planner Agent",
    desc: "Parses NL query, detects intent (stats/viz/analysis), identifies region & time filters, generates execution plan",
    color: "border-purple-500/40 bg-purple-500/5",
    dot: "bg-purple-500",
  },
  {
    step: "02",
    name: "Executor Agent",
    desc: "Orchestrates tools — ChromaDB semantic retrieval + PostgreSQL SQL execution + Analyzer calculations",
    color: "border-cyan-500/40 bg-cyan-500/5",
    dot: "bg-cyan-500",
  },
  {
    step: "03",
    name: "Synthesizer Agent",
    desc: "Calls Ollama LLM (qwen2:1.5b) to generate a natural language summary from retrieved data and analysis results",
    color: "border-emerald-500/40 bg-emerald-500/5",
    dot: "bg-emerald-500",
  },
  {
    step: "04",
    name: "Plotting Agent",
    desc: "Detects visualization need, generates interactive Plotly charts (T-S diagram, depth profile, map, time series)",
    color: "border-orange-500/40 bg-orange-500/5",
    dot: "bg-orange-500",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-ocean-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 nav-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">🌊</span>
            <span className="font-bold text-white text-lg tracking-tight">
              Float<span className="gradient-text">Chat</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#features" className="hover:text-cyan-400 transition-colors">Features</a>
            <a href="#demo" className="hover:text-cyan-400 transition-colors">Live Demo</a>
            <a href="#visualizations" className="hover:text-cyan-400 transition-colors">Visualizations</a>
            <a href="#architecture" className="hover:text-cyan-400 transition-colors">Architecture</a>
            <Link href="/about" className="hover:text-cyan-400 transition-colors">About</Link>
            <Link href="/docs" className="hover:text-cyan-400 transition-colors">API Docs</Link>
            <Link href="/status" className="hover:text-cyan-400 transition-colors">Status</Link>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/rZk1809/FloatChat"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
              className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg bg-ocean-700 border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all duration-200"
            >
              <Github size={16} />
              <span className="hidden sm:inline">GitHub</span>
            </a>
            <MobileNav />
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center wave-bg overflow-hidden pt-20">
        {/* Background orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/8 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-600/8 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "2s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/3 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-6 py-20">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-cyan-500/20 text-sm text-cyan-300 mb-8">
              <div className="pulse-dot" />
              <span>SIH 2025 — Smart India Hackathon Project</span>
            </div>

            {/* Title */}
            <h1 className="text-6xl md:text-8xl font-black text-white mb-6 leading-none tracking-tight">
              Float
              <span className="gradient-text text-glow">Chat</span>
            </h1>

            <p className="text-xl md:text-2xl text-slate-300 mb-4 font-light leading-relaxed">
              Intelligent Oceanographic Data Analysis
            </p>
            <p className="text-base md:text-lg text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              Multi-agent AI system for analyzing ARGO float data through natural language queries.
              Ask questions. Get insights. Generate visualizations — all powered by RAG.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <a
                href="#demo"
                className="flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold hover:from-cyan-400 hover:to-blue-500 transition-all duration-200 shadow-lg shadow-cyan-500/20 glow-cyan-sm"
              >
                <Zap size={18} />
                Try Live Demo
                <ArrowRight size={16} />
              </a>
              <a
                href="https://github.com/rZk1809/FloatChat"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-8 py-4 rounded-xl glass border border-cyan-500/20 text-slate-300 font-semibold hover:text-white hover:border-cyan-500/40 transition-all duration-200"
              >
                <Github size={18} />
                View Source
                <ExternalLink size={14} className="opacity-60" />
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {STATS.map(({ value, label, icon: Icon }) => (
                <div
                  key={label}
                  className="glass rounded-2xl p-5 border border-cyan-500/10 hover:border-cyan-500/25 transition-all duration-300 group"
                >
                  <Icon size={20} className="text-cyan-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                  <div className="text-2xl font-black gradient-text mb-1">
                    <AnimatedCounter to={value} />
                  </div>
                  <div className="text-xs text-slate-400">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-slate-600 animate-bounce">
            <span className="text-xs">Scroll to explore</span>
            <ChevronDown size={16} />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-400 mb-4">
              <Layers size={12} />
              SYSTEM CAPABILITIES
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              Built for{" "}
              <span className="gradient-text">Ocean Science</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              A complete AI-powered pipeline from natural language query to
              publishable oceanographic analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, description, color, badge }) => (
              <div
                key={title}
                className="feature-card glass rounded-2xl p-6 border border-cyan-500/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} p-0.5`}
                  >
                    <div className="w-full h-full rounded-[10px] bg-ocean-800/90 flex items-center justify-center">
                      <Icon size={22} className="text-white" />
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-ocean-700/80 text-slate-400 border border-slate-700/50">
                    {badge}
                  </span>
                </div>
                <h3 className="font-bold text-white mb-2 text-lg">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Demo Section */}
      <section id="demo" className="py-24 px-6 bg-ocean-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 mb-4">
              <div className="pulse-dot" style={{ background: "#10b981" }} />
              LIVE AI DEMO
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              Ask Anything About{" "}
              <span className="gradient-text">Ocean Data</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              Chat with FloatChat&apos;s AI assistant. Ask about ARGO float data,
              Indian Ocean dynamics, or the system&apos;s architecture.
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <ChatDemo />
          </div>

          <p className="text-center text-xs text-slate-600 mt-4">
            Powered by Claude AI (Anthropic) · For the full system with ARGO data queries, deploy locally with PostgreSQL + ChromaDB + Ollama
          </p>
        </div>
      </section>

      {/* Visualizations Section */}
      <section id="visualizations" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs text-purple-400 mb-4">
              <BarChart3 size={12} />
              GENERATED ANALYSES
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              <span className="gradient-text">17 Visualizations</span>
              <br />
              Generated by FloatChat
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              Every chart below was automatically generated by the FloatChat
              multi-agent system from real ARGO oceanographic data.
            </p>
          </div>

          <GallerySection plots={PLOTS} />
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className="py-24 px-6 bg-ocean-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs text-blue-400 mb-4">
              <Activity size={12} />
              HOW IT WORKS
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              Multi-Agent{" "}
              <span className="gradient-text">Architecture</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              A sequential pipeline of specialized AI agents transforms your natural
              language question into a complete oceanographic analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
            {ARCH_STEPS.map(({ step, name, desc, color, dot }) => (
              <div
                key={step}
                className={`rounded-2xl p-6 border ${color} relative`}
              >
                <div className="text-5xl font-black text-slate-700/50 mb-3">{step}</div>
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${dot}`} />
                  <h3 className="font-bold text-white text-sm">{name}</h3>
                </div>
                <p className="text-slate-400 text-xs leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Tech stack */}
          <div className="glass rounded-2xl p-8 border border-cyan-500/10">
            <h3 className="text-lg font-bold text-white mb-6 text-center">Technology Stack</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                {
                  category: "Data Layer",
                  items: ["PostgreSQL", "ChromaDB", "4,922 Embeddings"],
                  icon: Database,
                  color: "text-blue-400",
                },
                {
                  category: "AI & ML",
                  items: ["Ollama LLMs", "XGBoost", "K-Means", "Isolation Forest"],
                  icon: Brain,
                  color: "text-purple-400",
                },
                {
                  category: "Visualization",
                  items: ["Plotly", "Matplotlib", "Seaborn", "Cartopy"],
                  icon: BarChart3,
                  color: "text-emerald-400",
                },
                {
                  category: "Interface",
                  items: ["Streamlit", "CLI (Rich)", "PDF Export", "CSV Export"],
                  icon: Layers,
                  color: "text-cyan-400",
                },
              ].map(({ category, items, icon: Icon, color }) => (
                <div key={category}>
                  <div className="flex items-center gap-2 mb-3">
                    <Icon size={16} className={color} />
                    <span className="text-sm font-semibold text-slate-300">{category}</span>
                  </div>
                  <ul className="space-y-1.5">
                    {items.map((item) => (
                      <li key={item} className="text-xs text-slate-500 flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-slate-600 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Data Coverage Section */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-xs text-teal-400 mb-6">
                <Globe size={12} />
                GEOGRAPHIC COVERAGE
              </div>
              <h2 className="text-4xl font-black text-white mb-6">
                Indian Ocean
                <br />
                <span className="gradient-text">Data Coverage</span>
              </h2>
              <p className="text-slate-400 mb-8 leading-relaxed">
                FloatChat analyzes ARGO float data from four strategic ocean
                regions critical to Indian climate science and monsoon prediction.
              </p>
              <div className="space-y-4">
                {[
                  { region: "Bay of Bengal", coords: "5-25°N, 80-100°E", color: "bg-cyan-500", desc: "Critical for Indian monsoon dynamics and freshwater flux" },
                  { region: "Arabian Sea", coords: "5-25°N, 60-80°E", color: "bg-blue-500", desc: "Warm pool region, high salinity, strong evaporation" },
                  { region: "Indian Ocean", coords: "60°S-30°N, 20-120°E", color: "bg-teal-500", desc: "Full basin coverage including seasonal thermocline" },
                  { region: "Southern Ocean", coords: "80-40°S, global", color: "bg-indigo-500", desc: "Deep water formation, carbon sink dynamics" },
                ].map(({ region, coords, color, desc }) => (
                  <div key={region} className="flex gap-4 p-4 glass rounded-xl border border-cyan-500/10">
                    <div className={`w-2 rounded-full ${color} flex-shrink-0`} />
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-semibold text-white text-sm">{region}</span>
                        <span className="text-xs text-slate-500 font-mono">{coords}</span>
                      </div>
                      <p className="text-xs text-slate-400">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass rounded-2xl p-6 border border-cyan-500/10">
              <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <TrendingUp size={18} className="text-cyan-400" />
                ML Model Performance
              </h3>
              <div className="space-y-4">
                {[
                  { model: "XGBoost Temperature Prediction", metric: "R² Score", value: "0.97", bar: 97, color: "from-cyan-500 to-blue-500" },
                  { model: "K-Means Clustering", metric: "Silhouette Score", value: "0.71", bar: 71, color: "from-purple-500 to-pink-500" },
                  { model: "Isolation Forest (Anomaly)", metric: "Contamination", value: "5%", bar: 95, color: "from-emerald-500 to-teal-500" },
                  { model: "ARIMA Time Series", metric: "MAPE", value: "< 3%", bar: 97, color: "from-orange-500 to-red-500" },
                ].map(({ model, metric, value, bar, color }) => (
                  <div key={model}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-sm text-slate-300">{model}</span>
                      <div className="text-right">
                        <span className="text-xs text-slate-500">{metric}: </span>
                        <span className={`text-sm font-bold bg-gradient-to-r ${color} bg-clip-text text-transparent`}>{value}</span>
                      </div>
                    </div>
                    <div className="h-1.5 bg-ocean-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r ${color} rounded-full`}
                        style={{ width: `${bar}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400 mb-4">
              <HelpCircle size={12} />
              FAQ
            </div>
            <h2 className="text-4xl font-black text-white mb-4">
              Frequently Asked{" "}
              <span className="gradient-text">Questions</span>
            </h2>
          </div>
          <div className="space-y-4">
            {[
              {
                q: "What is an ARGO float?",
                a: "ARGO floats are autonomous profiling instruments deployed throughout the world's oceans. They drift at depth (typically ~1000m), then dive to 2000m and rise to the surface, measuring temperature, salinity, and pressure along the way. Data is transmitted via satellite.",
              },
              {
                q: "Can I query the real ARGO database through the live demo?",
                a: "The live demo on this website uses Claude AI to answer questions about FloatChat and ocean science. To run actual ARGO data queries (retrieving profiles, running ML models, generating plots), you need to deploy FloatChat locally with PostgreSQL, ChromaDB, and Ollama — see the GitHub repo for instructions.",
              },
              {
                q: "What oceanographic regions does FloatChat cover?",
                a: "FloatChat analyzes 4,922 ARGO profiles from the Bay of Bengal (5-25°N, 80-100°E), Arabian Sea (5-25°N, 60-80°E), broader Indian Ocean, and Southern Ocean. These regions are critical for Indian monsoon prediction and climate science.",
              },
              {
                q: "How does the multi-agent pipeline work?",
                a: "Your query goes through four agents: (1) Planner — parses intent and generates an execution plan; (2) Executor — runs tools (ChromaDB search, PostgreSQL queries, analysis); (3) Synthesizer — generates a natural language summary via Ollama; (4) Plotting Agent — creates visualizations if needed.",
              },
              {
                q: "What ML models are included?",
                a: "FloatChat includes XGBoost for temperature prediction (R²=0.97), K-Means clustering for water mass detection (k=4 optimal, silhouette=0.71), Isolation Forest for anomaly detection, ARIMA/SARIMA for time-series forecasting, and SHAP/PDP for explainability.",
              },
              {
                q: "Is the code open source?",
                a: "Yes! FloatChat is released under the MIT License. The full source code including the multi-agent pipeline, ML models, Next.js web app, and data ingestion scripts is available on GitHub.",
              },
            ].map(({ q, a }) => (
              <details
                key={q}
                className="group glass rounded-xl border border-cyan-500/10 overflow-hidden"
              >
                <summary className="flex items-center justify-between px-5 py-4 cursor-pointer list-none hover:bg-ocean-700/20 transition-colors">
                  <span className="font-semibold text-white text-sm pr-4">{q}</span>
                  <ChevronDown
                    size={16}
                    className="text-cyan-400 flex-shrink-0 transition-transform duration-200 group-open:rotate-180"
                  />
                </summary>
                <div className="px-5 pb-4">
                  <p className="text-slate-400 text-sm leading-relaxed">{a}</p>
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 border-t border-cyan-500/8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="text-center md:text-left">
              <div className="flex items-center gap-2 justify-center md:justify-start mb-2">
                <span className="text-2xl">🌊</span>
                <span className="font-bold text-white text-xl">
                  Float<span className="gradient-text">Chat</span>
                </span>
              </div>
              <p className="text-slate-500 text-sm max-w-md">
                Intelligent ARGO oceanographic data analysis powered by multi-agent AI.
                Built for SIH 2025.
              </p>
              <p className="text-slate-600 text-xs mt-2">
                © 2025 Rohith Ganesh Kanchi (RGK1809) · MIT License
              </p>
            </div>
            <div className="flex flex-col items-center gap-4">
              <div className="flex flex-wrap gap-3 justify-center">
                <a
                  href="https://github.com/rZk1809/FloatChat"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all duration-200"
                >
                  <Github size={15} />
                  GitHub
                </a>
                <Link
                  href="/about"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all duration-200"
                >
                  <Info size={15} />
                  About
                </Link>
                <Link
                  href="/docs"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all duration-200"
                >
                  <BookOpen size={15} />
                  API Docs
                </Link>
                <Link
                  href="/data"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all duration-200"
                >
                  <Database size={15} />
                  Data
                </Link>
                <Link
                  href="#demo"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600/80 to-blue-700/80 border border-cyan-500/30 text-sm text-white hover:from-cyan-500/80 hover:to-blue-600/80 transition-all duration-200"
                >
                  <Zap size={15} />
                  Try Demo
                </Link>
              </div>
              <p className="text-xs text-slate-600">
                Deployed on Vercel · Powered by Anthropic Claude
              </p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
