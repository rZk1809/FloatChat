"use client";

import { useEffect, useCallback } from "react";
import Image from "next/image";
import { X, ZoomIn, Download } from "lucide-react";

interface PlotModalProps {
  file: string;
  title: string;
  category: string;
  onClose: () => void;
}

export default function PlotModal({ file, title, category, onClose }: PlotModalProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="relative max-w-4xl w-full glass rounded-2xl overflow-hidden border border-cyan-500/20 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-cyan-500/10 bg-ocean-800/50">
          <div>
            <span className="text-xs text-cyan-400/70 block">{category}</span>
            <p className="font-semibold text-white text-sm">{title}</p>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={`/plots/${file}`}
              download={file}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white bg-ocean-700/50 border border-slate-700/50 hover:border-cyan-500/30 transition-colors"
              onClick={(e) => e.stopPropagation()}
              aria-label={`Download ${title}`}
            >
              <Download size={12} />
              Download
            </a>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-ocean-600/60 transition-colors"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Image */}
        <div className="relative bg-ocean-800/30 p-4">
          <Image
            src={`/plots/${file}`}
            alt={title}
            width={900}
            height={675}
            className="w-full h-auto rounded-lg object-contain max-h-[70vh]"
            priority
          />
        </div>

        <p className="text-center text-xs text-slate-600 pb-3">
          Press Esc or click outside to close · <ZoomIn size={10} className="inline" /> Click to download
        </p>
      </div>
    </div>
  );
}
