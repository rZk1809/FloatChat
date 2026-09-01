import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-500">
      <Link href="/" className="flex items-center gap-1 hover:text-cyan-400 transition-colors">
        <Home size={12} />
        <span>Home</span>
      </Link>
      {items.map(({ label, href }, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <ChevronRight size={12} className="text-slate-700" />
          {href ? (
            <Link href={href} className="hover:text-cyan-400 transition-colors">
              {label}
            </Link>
          ) : (
            <span className="text-slate-300">{label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
