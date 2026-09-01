import type { Metadata } from "next";
import "./globals.css";
import PageProgressBar from "@/components/PageProgressBar";
import BackToTop from "@/components/BackToTop";
import SkipToContent from "@/components/SkipToContent";

const JSONLD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "FloatChat",
  description:
    "AI-powered ARGO oceanographic float data analysis using a multi-agent RAG pipeline.",
  applicationCategory: "ScienceApplication",
  operatingSystem: "Web",
  author: {
    "@type": "Person",
    name: "Rohith Ganesh Kanchi",
    url: "https://github.com/rZk1809",
  },
  license: "https://opensource.org/licenses/MIT",
  codeRepository: "https://github.com/rZk1809/FloatChat",
  keywords: "ARGO floats, oceanography, AI, RAG, Indian Ocean, Bay of Bengal",
};

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
  manifest: "/manifest.json",
  themeColor: "#06b6d4",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSONLD) }}
        />
      </head>
      <body className="antialiased">
        <SkipToContent />
        <PageProgressBar />
        {children}
        <BackToTop />
      </body>
    </html>
  );
}
