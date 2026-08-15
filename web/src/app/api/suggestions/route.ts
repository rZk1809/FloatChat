import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

export const runtime = "edge";

const REGIONAL_SUGGESTIONS: Record<string, string[]> = {
  "bay of bengal": [
    "What is the average salinity in the Bay of Bengal?",
    "How deep is the thermocline in the Bay of Bengal?",
    "Compare Bay of Bengal and Arabian Sea temperature profiles",
  ],
  "arabian sea": [
    "Why is the Arabian Sea saltier than the Bay of Bengal?",
    "What is the mixed layer depth in the Arabian Sea?",
    "How does Arabian Sea upwelling affect temperature profiles?",
  ],
  "southern ocean": [
    "How does the Southern Ocean contribute to deep water formation?",
    "What ARGO profiles were collected in the Southern Ocean?",
    "How cold is the Southern Ocean surface temperature?",
  ],
  "indian ocean": [
    "What is the seasonal thermocline variation in the Indian Ocean?",
    "How many ARGO floats are active in the Indian Ocean?",
    "What water masses exist in the Indian Ocean?",
  ],
};

const TOPIC_SUGGESTIONS: Record<string, string[]> = {
  "cluster": [
    "How were the 4 water mass clusters determined?",
    "What oceanographic properties define each cluster?",
    "Show me the geographic distribution of clusters",
  ],
  "xgboost": [
    "What is the XGBoost model accuracy on test data?",
    "Which features are most important for temperature prediction?",
    "How are partial dependence plots interpreted?",
  ],
  "anomal": [
    "How many anomalous profiles were detected?",
    "What physical processes cause anomalous ARGO readings?",
    "Where geographically do anomalies cluster?",
  ],
  "rag": [
    "How does ChromaDB semantic search work?",
    "What is the difference between RAG and traditional search?",
    "How many embeddings are stored in ChromaDB?",
  ],
};

const DEFAULT_SUGGESTIONS = [
  "What is the thermocline and why does it matter?",
  "How does ARGO float profiling work mechanically?",
  "What is a T-S diagram and how do you read it?",
  "Compare temperature and salinity across ocean regions",
  "How does FloatChat detect oceanographic anomalies?",
];

const requestSchema = z.object({
  context: z.string().max(2000).optional(),
});

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ suggestions: DEFAULT_SUGGESTIONS });
  }

  const parsed = requestSchema.safeParse(body);
  const context = parsed.success ? (parsed.data.context ?? "") : "";
  const lower = context.toLowerCase();

  const suggestions: string[] = [];

  for (const [key, vals] of Object.entries(REGIONAL_SUGGESTIONS)) {
    if (lower.includes(key)) {
      suggestions.push(...vals);
      break;
    }
  }

  if (suggestions.length < 3) {
    for (const [key, vals] of Object.entries(TOPIC_SUGGESTIONS)) {
      if (lower.includes(key)) {
        suggestions.push(...vals);
        break;
      }
    }
  }

  const result = suggestions.length >= 3
    ? suggestions.slice(0, 5)
    : DEFAULT_SUGGESTIONS;

  return NextResponse.json({ suggestions: result });
}
