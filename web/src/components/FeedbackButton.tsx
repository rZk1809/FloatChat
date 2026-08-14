"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { cn } from "@/lib/cn";

interface FeedbackButtonProps {
  messageIndex: number;
  query?: string;
}

type Rating = "up" | "down" | null;

export default function FeedbackButton({ messageIndex, query }: FeedbackButtonProps) {
  const [rating, setRating] = useState<Rating>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleRate = async (r: "up" | "down") => {
    if (submitted) return;
    setRating(r);
    setSubmitted(true);
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: r, messageIndex, query }),
      });
    } catch {
      // Fire-and-forget — ignore errors
    }
  };

  return (
    <div className="flex items-center gap-1" aria-label="Rate this response">
      <button
        onClick={() => handleRate("up")}
        disabled={submitted}
        className={cn(
          "w-6 h-6 rounded flex items-center justify-center transition-all duration-200",
          "text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10",
          "focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-400",
          "disabled:cursor-default",
          rating === "up" && "text-emerald-400 bg-emerald-500/10"
        )}
        aria-label="Helpful"
        aria-pressed={rating === "up"}
      >
        <ThumbsUp size={12} />
      </button>
      <button
        onClick={() => handleRate("down")}
        disabled={submitted}
        className={cn(
          "w-6 h-6 rounded flex items-center justify-center transition-all duration-200",
          "text-slate-500 hover:text-red-400 hover:bg-red-500/10",
          "focus:outline-none focus-visible:ring-1 focus-visible:ring-red-400",
          "disabled:cursor-default",
          rating === "down" && "text-red-400 bg-red-500/10"
        )}
        aria-label="Not helpful"
        aria-pressed={rating === "down"}
      >
        <ThumbsDown size={12} />
      </button>
    </div>
  );
}
