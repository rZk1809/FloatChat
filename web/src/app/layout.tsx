import type { Metadata } from "next";
import "./globals.css";
import PageProgressBar from "@/components/PageProgressBar";

export const metadata: Metadata = {
  title: "FloatChat — Intelligent Oceanographic Data Analysis",
  description:
    "AI-powered ARGO float data analysis using multi-agent RAG architecture. Analyze ocean temperature, salinity, and pressure data through natural language queries.",
  keywords: [
    "ARGO floats",
    "oceanography",
    "AI",
    "RAG",
    "multi-agent",
    "Indian Ocean",
    "Bay of Bengal",
    "data analysis",
  ],
  authors: [{ name: "Rohith Ganesh Kanchi", url: "https://github.com/rZk1809" }],
  openGraph: {
    title: "FloatChat — Intelligent Oceanographic Data Analysis",
    description:
      "AI-powered ARGO float data analysis using multi-agent RAG architecture",
    type: "website",
  },
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌊</text></svg>",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="antialiased">
        <PageProgressBar />
        {children}
      </body>
    </html>
  );
}
