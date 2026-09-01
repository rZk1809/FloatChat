import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowLeft,
  Database,
  Thermometer,
  Droplets,
  Layers,
  Globe,
  TrendingUp,
  BarChart3,
  Activity,
} from "lucide-react";
import { OCEAN_REGIONS, DATASET_STATS, ML_METRICS } from "@/lib/constants";
import Breadcrumb from "@/components/Breadcrumb";

export const metadata: Metadata = {
  title: "Data Explorer — FloatChat",
  description:
    "Explore ARGO float dataset statistics, ocean region coverage, depth profiles, and ML model metrics for the FloatChat system.",
};

const DEPTH_LAYERS = [
  { name: "Surface", range: "0–10 m", temp: "27–30°C", sal: "32–37 PSU", color: "from-cyan-400 to-teal-500" },
  { name: "Mixed Layer", range: "10–150 m", temp: "22–29°C", sal: "33–37 PSU", color: "from-teal-400 to-blue-500" },
  { name: "Thermocline", range: "150–500 m", temp: "10–22°C", sal: "34–37 PSU", color: "from-blue-400 to-indigo-500" },
  { name: "Deep Ocean", range: "500–2000 m", temp: "2–10°C", sal: "34–35 PSU", color: "from-indigo-400 to-purple-500" },
];

const REGION_COLOR_MAP: Record<string, string> = {
  cyan: "border-cyan-500/40 bg-cyan-500/5",
  blue: "border-blue-500/40 bg-blue-500/5",
  teal: "border-teal-500/40 bg-teal-500/5",
  indigo: "border-indigo-500/40 bg-indigo-500/5",
};

const REGION_TEXT_MAP: Record<string, string> = {
  cyan: "text-cyan-400",
  blue: "text-blue-400",
  teal: "text-teal-400",
  indigo: "text-indigo-400",
};

const REGION_BAR_MAP: Record<string, string> = {
  cyan: "bg-cyan-500",
  blue: "bg-blue-500",
  teal: "bg-teal-500",
  indigo: "bg-indigo-500",
};

export default function DataPage() {
  const total = DATASET_STATS.totalProfiles;

  return (
    <main className="min-h-screen bg-ocean-950 pt-24 pb-20 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <Breadcrumb items={[{ label: "Data Explorer" }]} />
        </div>

        <div className="flex items-center gap-4 mb-10">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft size={16} />
            Back
          </Link>
        </div>

        <div className="mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-400 mb-4">
            <Database size={12} />
            ARGO DATASET
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white mb-4">
            Data <span className="gradient-text">Explorer</span>
          </h1>
          <p className="text-slate-400 max-w-2xl text-lg">
            Interactive overview of the {total.toLocaleString()} ARGO float profiles
            powering FloatChat&apos;s oceanographic analysis.
          </p>
        </div>

        {/* Top-level stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            { icon: Database, label: "Total Profiles", value: total.toLocaleString(), sub: "ARGO float casts" },
            { icon: Globe, label: "Ocean Regions", value: "4", sub: "Indian Ocean basin" },
            { icon: Layers, label: "Max Depth", value: "2,000 m", sub: "pressure measurements" },
            { icon: Activity, label: "Date Range", value: "25 yrs", sub: "2000–2025" },
          ].map(({ icon: Icon, label, value, sub }) => (
            <div key={label} className="glass rounded-2xl p-5 border border-cyan-500/10">
              <Icon size={18} className="text-cyan-400 mb-3" />
              <p className="text-2xl font-black gradient-text">{value}</p>
              <p className="text-xs font-semibold text-slate-300 mt-1">{label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>

        {/* Region breakdown */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Globe size={20} className="text-cyan-400" />
            Regional Coverage
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {OCEAN_REGIONS.map((r) => {
              const pct = Math.round((r.profiles / total) * 100);
              return (
                <div
                  key={r.name}
                  className={`rounded-2xl p-5 border ${REGION_COLOR_MAP[r.color]}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className={`font-bold text-white mb-0.5`}>{r.name}</h3>
                      <p className="text-xs font-mono text-slate-500">{r.coords}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full bg-ocean-700/80 ${REGION_TEXT_MAP[r.color]} font-bold`}>
                      {pct}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mb-4 leading-relaxed">{r.desc}</p>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Profiles</span>
                      <span className="font-bold text-slate-200">{r.profiles.toLocaleString()}</span>
                    </div>
                    <div className="h-1.5 bg-ocean-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${REGION_BAR_MAP[r.color]} rounded-full`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="flex gap-4 text-slate-500 pt-1">
                      <span className="flex items-center gap-1">
                        <Thermometer size={10} />
                        Avg {r.avgSurfaceTemp}°C
                      </span>
                      <span className="flex items-center gap-1">
                        <Droplets size={10} />
                        {r.avgSalinity} PSU
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Depth layers */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Layers size={20} className="text-cyan-400" />
            Depth Profile Structure
          </h2>
          <div className="space-y-3">
            {DEPTH_LAYERS.map((layer, i) => (
              <div key={layer.name} className="glass rounded-xl p-4 border border-cyan-500/10 flex items-center gap-5">
                <div className={`w-1 self-stretch rounded-full bg-gradient-to-b ${layer.color} flex-shrink-0`} />
                <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div>
                    <p className="text-slate-500 mb-0.5">Layer</p>
                    <p className="font-bold text-white">{layer.name}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 mb-0.5">Depth</p>
                    <p className="font-mono text-slate-300">{layer.range}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 mb-0.5">Temperature</p>
                    <p className="text-slate-300">{layer.temp}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 mb-0.5">Salinity</p>
                    <p className="text-slate-300">{layer.sal}</p>
                  </div>
                </div>
                <span className="text-2xl font-black text-slate-700/40 flex-shrink-0">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ML metrics */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <TrendingUp size={20} className="text-cyan-400" />
            ML Model Metrics
          </h2>
          <div className="glass rounded-2xl p-6 border border-cyan-500/10 space-y-5">
            {ML_METRICS.map(({ model, metric, value, bar }) => (
              <div key={model}>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-sm text-slate-300">{model}</span>
                  <div className="text-right">
                    <span className="text-xs text-slate-500">{metric}: </span>
                    <span className="text-sm font-bold gradient-text">{value}</span>
                  </div>
                </div>
                <div className="h-1.5 bg-ocean-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                    style={{ width: `${bar}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Variables measured */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <BarChart3 size={20} className="text-cyan-400" />
            Measured Variables
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                icon: Thermometer,
                variable: "Temperature",
                unit: "°C",
                range: "-2 to 32°C",
                precision: "0.001°C",
                color: "text-orange-400",
              },
              {
                icon: Droplets,
                variable: "Salinity",
                unit: "PSU",
                range: "30–40 PSU",
                precision: "0.001 PSU",
                color: "text-blue-400",
              },
              {
                icon: Activity,
                variable: "Pressure",
                unit: "dbar",
                range: "0–2000 dbar",
                precision: "1 dbar",
                color: "text-purple-400",
              },
            ].map(({ icon: Icon, variable, unit, range, precision, color }) => (
              <div key={variable} className="glass rounded-xl p-5 border border-cyan-500/10">
                <Icon size={22} className={`${color} mb-3`} />
                <h3 className="font-bold text-white mb-1">{variable}</h3>
                <p className="text-xs text-slate-500 mb-3">Unit: {unit}</p>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Range</span>
                    <span className="text-slate-300 font-mono">{range}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Precision</span>
                    <span className="text-slate-300 font-mono">{precision}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
