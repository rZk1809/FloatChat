import { NextResponse } from "next/server";
import { OCEAN_REGIONS } from "@/lib/constants";

export const runtime = "edge";

export async function GET() {
  return NextResponse.json({
    regions: OCEAN_REGIONS,
    total: OCEAN_REGIONS.length,
  });
}
