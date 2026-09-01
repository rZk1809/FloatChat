"use client";

import { useState } from "react";
import Image from "next/image";
import { ZoomIn, Search, X } from "lucide-react";
import PlotModal from "./PlotModal";
import { useDebounce } from "@/hooks/useDebounce";

interface Plot {
  file: string;
  title: string;
  category: string;
}

const CATEGORIES = ["All", "Clustering", "Analysis", "ML", "XAI"] as const;
type Category = (typeof CATEGORIES)[number];

interface GallerySectionProps {
  plots: Plot[];
}

export default function GallerySection({ plots }: GallerySectionProps) {
  const [activeCategory, setActiveCategory] = useState<Category>("All");
  const [selectedPlot, setSelectedPlot] = useState<Plot | null>(null);
  const [searchRaw, setSearchRaw] = useState("");
  const search = useDebounce(searchRaw, 200);

  const filtered = plots
    .filter((p) => activeCategory === "All" || p.category === activeCategory)
    .filter((p) => {
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return p.title.toLowerCase().includes(q) || p.category.toLowerCase().includes(q);
    });

  return (
    <>
      {/* Search + Category filters */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
        {/* Search */}
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            type="search"
            value={searchRaw}
            onChange={(e) => setSearchRaw(e.target.value)}
            placeholder="Search plots…"
            aria-label="Search visualizations"
            className="pl-8 pr-8 py-1.5 rounded-full text-xs bg-ocean-700/60 border border-cyan-500/15 text-slate-300 placeholder-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus:border-cyan-500/40 transition-all w-48"
          />
          {searchRaw && (
            <button
              onClick={() => setSearchRaw("")}
              aria-label="Clear search"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Category pills */}
        <div className="flex flex-wrap gap-2 justify-center">
          {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-3 py-1.5 rounded-full text-xs border transition-all duration-200 ${
              activeCategory === cat
                ? "border-cyan-500/60 text-cyan-300 bg-cyan-500/10"
                : "border-cyan-500/15 text-slate-400 bg-ocean-800/50 hover:border-cyan-500/30 hover:text-slate-300"
            }`}
          >
            {cat}
            {cat !== "All" && (
                <span className="ml-1.5 opacity-60">
                  ({plots.filter((p) => p.category === cat).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-slate-500 text-sm py-10">
          No visualizations match &ldquo;{search}&rdquo;
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map(({ file, title, category }) => (
          <button
            key={file}
            onClick={() => setSelectedPlot({ file, title, category })}
            className="plot-card glass rounded-xl overflow-hidden border border-cyan-500/10 group text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
            aria-label={`View ${title}`}
          >
            <div className="aspect-[4/3] overflow-hidden bg-ocean-800/50 relative">
              <Image
                src={`/plots/${file}`}
                alt={title}
                width={400}
                height={300}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black/30">
                <div className="w-10 h-10 rounded-full bg-cyan-500/80 flex items-center justify-center">
                  <ZoomIn size={18} className="text-white" />
                </div>
              </div>
            </div>
            <div className="p-3">
              <div className="text-xs text-cyan-400/70 mb-1">{category}</div>
              <p className="text-xs text-slate-300 font-medium leading-tight">{title}</p>
            </div>
          </button>
        ))}
      </div>

      {selectedPlot && (
        <PlotModal
          file={selectedPlot.file}
          title={selectedPlot.title}
          category={selectedPlot.category}
          onClose={() => setSelectedPlot(null)}
        />
      )}
    </>
  );
}
