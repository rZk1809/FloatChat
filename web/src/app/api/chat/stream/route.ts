import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";
import { z } from "zod";

const SYSTEM_PROMPT = `You are FloatChat, an expert AI assistant for oceanographic data analysis. You specialize in ARGO float data — autonomous profiling floats that drift through ocean currents, measuring temperature, salinity, and pressure from surface to 2000m depth.

About the FloatChat system you represent:
- Analyzes 4,922 ARGO oceanographic profiles in Indian Ocean waters
- Coverage: Bay of Bengal (5-25°N, 80-100°E), Arabian Sea (5-25°N, 60-80°E), broader Indian Ocean, Southern Ocean
- Multi-agent AI pipeline: Planner → Executor → Synthesizer → Plotting Agent
- Combines ChromaDB vector search with PostgreSQL for hybrid retrieval
- Generates T-S diagrams, temperature-depth profiles, geographic maps, and time-series plots
- Uses XGBoost for temperature prediction, K-means clustering (k=4 optimal), Isolation Forest for anomalies
- Built for SIH 2025 (Smart India Hackathon 2025) by Rohith Ganesh Kanchi

Be helpful, scientifically accurate, and engaging. Keep responses concise but informative. Use markdown when helpful.`;

const MAX_MESSAGES = 20;
const MAX_CONTENT_LENGTH = 4000;

const chatRequestSchema = z.object({
  messages: z
    .array(
      z.object({
        role: z.enum(["user", "assistant"]),
        content: z.string().min(1).max(MAX_CONTENT_LENGTH),
      })
    )
    .min(1)
    .max(MAX_MESSAGES),
});

const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 20;
const store = new Map<string, { count: number; windowStart: number }>();
let cleanupCounter = 0;

function checkRateLimit(key: string) {
  const now = Date.now();
  cleanupCounter += 1;
  if (cleanupCounter >= 100) {
    cleanupCounter = 0;
    store.forEach((e, k) => { if (now - e.windowStart >= RATE_LIMIT_WINDOW_MS) store.delete(k); });
  }
  const entry = store.get(key);
  if (!entry || now - entry.windowStart >= RATE_LIMIT_WINDOW_MS) {
    store.set(key, { count: 1, windowStart: now });
    return true;
  }
  if (entry.count >= RATE_LIMIT_MAX) return false;
  entry.count += 1;
  return true;
}

function getClientKey(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    req.ip ||
    "unknown"
  );
}

export async function POST(req: NextRequest) {
  const clientKey = getClientKey(req);
  if (!checkRateLimit(clientKey)) {
    return new Response(
      `data: ${JSON.stringify({ error: "Rate limit exceeded" })}\n\ndata: [DONE]\n\n`,
      { status: 429, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return new Response(
      `data: ${JSON.stringify({ error: "Invalid JSON" })}\n\ndata: [DONE]\n\n`,
      { status: 400, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  const parsed = chatRequestSchema.safeParse(body);
  if (!parsed.success) {
    const msg = parsed.error.issues[0]?.message ?? "Invalid request";
    return new Response(
      `data: ${JSON.stringify({ error: msg })}\n\ndata: [DONE]\n\n`,
      { status: 400, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return new Response(
      `data: ${JSON.stringify({ error: "ANTHROPIC_API_KEY not configured" })}\n\ndata: [DONE]\n\n`,
      { status: 500, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  const stream = new ReadableStream({
    async start(controller) {
      const enc = new TextEncoder();
      try {
        const sdkStream = await client.messages.stream({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 1024,
          system: SYSTEM_PROMPT,
          messages: parsed.data.messages.map((m) => ({ role: m.role, content: m.content })),
        });

        for await (const event of sdkStream) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            controller.enqueue(
              enc.encode(`data: ${JSON.stringify({ delta: event.delta.text })}\n\n`)
            );
          }
        }
        controller.enqueue(enc.encode("data: [DONE]\n\n"));
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Streaming error";
        controller.enqueue(enc.encode(`data: ${JSON.stringify({ error: msg })}\n\ndata: [DONE]\n\n`));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
