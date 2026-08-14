import { cn } from "@/lib/cn";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-ocean-700/50",
        className
      )}
    />
  );
}

export function ChatMessageSkeleton() {
  return (
    <div className="flex gap-3">
      <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  );
}

export function PlotCardSkeleton() {
  return (
    <div className="glass rounded-xl overflow-hidden border border-cyan-500/10">
      <Skeleton className="aspect-[4/3] w-full" />
      <div className="p-3 space-y-1.5">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-32" />
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="glass rounded-2xl p-5 border border-cyan-500/10">
      <Skeleton className="w-5 h-5 rounded mx-auto mb-2" />
      <Skeleton className="h-7 w-16 mx-auto mb-1" />
      <Skeleton className="h-3 w-20 mx-auto" />
    </div>
  );
}
