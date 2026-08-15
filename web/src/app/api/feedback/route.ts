import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

export const runtime = "edge";

const feedbackSchema = z.object({
  rating: z.enum(["up", "down"]),
  messageIndex: z.number().int().min(0),
  query: z.string().max(500).optional(),
  comment: z.string().max(500).optional(),
});

// Simple in-memory counter (resets on cold starts — fine for a demo)
const counts = { up: 0, down: 0 };

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const parsed = feedbackSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid feedback payload" }, { status: 400 });
  }

  const { rating } = parsed.data;
  counts[rating] += 1;

  return NextResponse.json({ received: true, rating, totals: { ...counts } });
}

export async function GET() {
  return NextResponse.json({ totals: { ...counts } });
}
