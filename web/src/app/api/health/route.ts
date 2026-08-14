import { NextResponse } from "next/server";

export const runtime = "edge";

const VERSION = "1.2.0";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    version: VERSION,
    timestamp: new Date().toISOString(),
    services: {
      chat: !!process.env.ANTHROPIC_API_KEY,
    },
  });
}
