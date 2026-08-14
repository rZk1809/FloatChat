import Link from "next/link";
import { Home, Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-ocean-950 flex items-center justify-center px-6">
      <div className="text-center max-w-lg">
        <div className="text-8xl font-black gradient-text mb-4">404</div>
        <div className="text-4xl mb-6">🌊</div>
        <h1 className="text-2xl font-bold text-white mb-3">Page Not Found</h1>
        <p className="text-slate-400 mb-8 leading-relaxed">
          This page drifted off like an ARGO float into the deep ocean.
          Let&apos;s navigate back to familiar waters.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold hover:from-cyan-400 hover:to-blue-500 transition-all duration-200"
          >
            <Home size={16} />
            Back to Home
          </Link>
          <Link
            href="/#demo"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl glass border border-cyan-500/20 text-slate-300 font-semibold hover:text-white hover:border-cyan-500/40 transition-all duration-200"
          >
            <Search size={16} />
            Try Live Demo
          </Link>
        </div>
      </div>
    </main>
  );
}
