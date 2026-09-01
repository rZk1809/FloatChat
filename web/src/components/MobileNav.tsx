"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Menu, X, Github, Zap } from "lucide-react";

const NAV_LINKS = [
  { href: "/#features", label: "Features" },
  { href: "/#demo", label: "Live Demo" },
  { href: "/#visualizations", label: "Visualizations" },
  { href: "/#architecture", label: "Architecture" },
  { href: "/about", label: "About" },
  { href: "/docs", label: "API Docs" },
  { href: "/status", label: "Status" },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Open navigation menu"
        className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-ocean-700/60 transition-colors"
      >
        <Menu size={20} />
      </button>

      {open && (
        <div className="fixed inset-0 z-[200] md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Drawer */}
          <div className="absolute top-0 right-0 h-full w-72 bg-ocean-900 border-l border-cyan-500/15 flex flex-col shadow-2xl animate-slide-in">
            <div className="flex items-center justify-between px-5 py-4 border-b border-cyan-500/10">
              <div className="flex items-center gap-2">
                <span className="text-xl">🌊</span>
                <span className="font-bold text-white">
                  Float<span className="gradient-text">Chat</span>
                </span>
              </div>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close navigation menu"
                className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-ocean-700/60 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <nav className="flex-1 overflow-y-auto py-4">
              {NAV_LINKS.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className="flex items-center px-5 py-3 text-slate-300 hover:text-white hover:bg-ocean-700/40 transition-colors text-sm font-medium"
                >
                  {label}
                </Link>
              ))}
            </nav>

            <div className="px-5 py-4 border-t border-cyan-500/10 space-y-3">
              <a
                href="https://github.com/rZk1809/FloatChat"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 w-full px-4 py-2.5 rounded-xl glass border border-cyan-500/20 text-sm text-slate-300 hover:text-white transition-all"
              >
                <Github size={15} />
                GitHub
              </a>
              <a
                href="/#demo"
                onClick={() => setOpen(false)}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-sm text-white font-semibold hover:from-cyan-400 hover:to-blue-500 transition-all"
              >
                <Zap size={15} />
                Try Demo
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
