import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
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

You can answer questions about:
1. ARGO float data and what it measures
2. Oceanographic concepts (thermocline, halocline, T-S diagrams, stratification, mixed layer depth)
3. Indian Ocean, Bay of Bengal, Arabian Sea dynamics and patterns
4. How to interpret oceanographic data visualizations
5. The FloatChat system architecture and capabilities
6. Data analysis methodologies used (RAG, clustering, anomaly detection, time series)
7. Temperature and salinity statistics in the covered regions

Sample statistics from the dataset:
- Bay of Bengal avg surface temp: ~28-29°C
- Arabian Sea avg surface temp: ~27-28°C
- Thermocline depth: typically 50-150m
- Salinity range: 33-37 PSU depending on region
- 4 distinct water mass clusters identified

Be helpful, scientifically accurate, and engaging. Keep responses concise but informative. Use markdown formatting when helpful.`;

// ---------------------------------------------------------------------------
// Request validation
// ---------------------------------------------------------------------------

const MAX_MESSAGES = 20;
const MAX_CONTENT_LENGTH = 4000;

const chatMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z
    .string()
    .min(1, "Message content cannot be empty")
    .max(
      MAX_CONTENT_LENGTH,
      `Message content cannot exceed ${MAX_CONTENT_LENGTH} characters`
    ),
});

const chatRequestSchema = z.object({
  messages: z
    .array(chatMessageSchema)
    .min(1, "messages must be a non-empty array")
    .max(MAX_MESSAGES, `messages cannot contain more than ${MAX_MESSAGES} entries`),
});

// ---------------------------------------------------------------------------
// Rate limiting
//
// This is a simple in-memory, per-process, IP-keyed sliding-window limiter.
// It is intentionally minimal — good enough to stop naive abuse of this demo
// endpoint (e.g. a script hammering it directly, bypassing the client-side
// `.slice(-10)` guard) — but it has real limitations callers should know
// about before relying on it in production:
//
//   - State lives in a plain in-memory Map, so it resets on every
//     redeploy/restart.
//   - On a platform that runs multiple serverless/edge instances (e.g.
//     Vercel), each instance has its own independent counters, so the
//     *effective* limit is (per-instance limit) × (number of warm
//     instances), not a true global limit.
//
// A real deployment that needs robust rate limiting should move this to a
// shared store — e.g. Upstash Redis (via @upstash/ratelimit) — or rely on
// Vercel's platform-level rate limiting / firewall rules instead.
// ---------------------------------------------------------------------------

const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 20;

interface RateLimitEntry {
  count: number;
  windowStart: number;
}

const rateLimitStore = new Map<string, RateLimitEntry>();

let requestsSinceCleanup = 0;

/** Opportunistically evict expired entries so the Map doesn't grow forever. */
function cleanupExpiredEntries(now: number) {
  rateLimitStore.forEach((entry, key) => {
    if (now - entry.windowStart >= RATE_LIMIT_WINDOW_MS) {
      rateLimitStore.delete(key);
    }
  });
}

function checkRateLimit(key: string): { allowed: boolean; retryAfterSeconds: number } {
  const now = Date.now();

  requestsSinceCleanup += 1;
  if (requestsSinceCleanup >= 100) {
    requestsSinceCleanup = 0;
    cleanupExpiredEntries(now);
  }

  const entry = rateLimitStore.get(key);

  if (!entry || now - entry.windowStart >= RATE_LIMIT_WINDOW_MS) {
    rateLimitStore.set(key, { count: 1, windowStart: now });
    return { allowed: true, retryAfterSeconds: 0 };
  }

  if (entry.count >= RATE_LIMIT_MAX_REQUESTS) {
    const retryAfterSeconds = Math.max(
      1,
      Math.ceil((entry.windowStart + RATE_LIMIT_WINDOW_MS - now) / 1000)
    );
    return { allowed: false, retryAfterSeconds };
  }

  entry.count += 1;
  return { allowed: true, retryAfterSeconds: 0 };
}

function getClientKey(req: NextRequest): string {
  const forwardedFor = req.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return forwardedFor.split(",")[0]?.trim() || "unknown";
  }
  const realIp = req.headers.get("x-real-ip");
  if (realIp) return realIp;
  if (req.ip) return req.ip;
  return "unknown";
}

export async function POST(req: NextRequest) {
  try {
    const clientKey = getClientKey(req);
    const rateLimit = checkRateLimit(clientKey);
    if (!rateLimit.allowed) {
      return NextResponse.json(
        { error: "Too many requests. Please wait a moment before trying again." },
        {
          status: 429,
          headers: { "Retry-After": String(rateLimit.retryAfterSeconds) },
        }
      );
    }

    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json(
        { error: "Request body must be valid JSON." },
        { status: 400 }
      );
    }

    const parsed = chatRequestSchema.safeParse(body);
    if (!parsed.success) {
      const message = parsed.error.issues[0]?.message ?? "Invalid request body.";
      return NextResponse.json({ error: message }, { status: 400 });
    }

    const { messages } = parsed.data;

    if (!process.env.ANTHROPIC_API_KEY) {
      return NextResponse.json(
        {
          error:
            "ANTHROPIC_API_KEY not configured. Please add your API key to continue.",
        },
        { status: 500 }
      );
    }

    const client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    const response = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1024,
      system: SYSTEM_PROMPT,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    });

    const textContent = response.content.find((c) => c.type === "text");
    return NextResponse.json({
      content: textContent ? textContent.text : "Unable to generate response.",
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: "Failed to process your request. Please try again." },
      { status: 500 }
    );
  }
}
