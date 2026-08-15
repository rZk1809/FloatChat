"use client";

import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import type { Toast, ToastType } from "@/hooks/useToast";

const ICONS: Record<ToastType, React.ElementType> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
};

const STYLES: Record<ToastType, string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  error: "border-red-500/30 bg-red-500/10 text-red-300",
  info: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
};

interface ToastProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastProps) {
  const Icon = ICONS[toast.type];
  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm backdrop-blur-md shadow-lg animate-slide-in ${STYLES[toast.type]}`}
      role="alert"
    >
      <Icon size={16} className="flex-shrink-0" />
      <span className="flex-1">{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss notification"
      >
        <X size={14} />
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export default function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem toast={t} onRemove={onRemove} />
        </div>
      ))}
    </div>
  );
}
