"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

export default function PageProgressBar() {
  const pathname = usePathname();
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    setProgress(20);

    const t1 = setTimeout(() => setProgress(60), 100);
    const t2 = setTimeout(() => setProgress(85), 300);
    const t3 = setTimeout(() => {
      setProgress(100);
      const t4 = setTimeout(() => setVisible(false), 300);
      return () => clearTimeout(t4);
    }, 500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [pathname]);

  if (!visible) return null;

  return (
    <div
      className="fixed top-0 left-0 z-[9999] h-[2px] bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-300 ease-out"
      style={{ width: `${progress}%`, opacity: progress === 100 ? 0 : 1 }}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
    />
  );
}
