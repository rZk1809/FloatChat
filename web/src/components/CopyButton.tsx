"use client";

import { useState, useCallback } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/cn";

interface CopyButtonProps {
  text: string;
  className?: string;
  size?: number;
}

export default function CopyButton({ text, className, size = 14 }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable
    }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "flex items-center justify-center w-7 h-7 rounded-lg transition-all duration-200",
        "text-slate-400 hover:text-cyan-300 hover:bg-ocean-600/60",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400",
        copied && "text-emerald-400 hover:text-emerald-400",
        className
      )}
      aria-label={copied ? "Copied!" : "Copy to clipboard"}
      title={copied ? "Copied!" : "Copy"}
    >
      {copied ? <Check size={size} /> : <Copy size={size} />}
    </button>
  );
}
