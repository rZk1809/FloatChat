import { describe, it, expect, beforeEach, vi } from "vitest";
import { GET } from "./route";

describe("GET /api/health", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns status ok", async () => {
    const res = await GET();
    const body = await res.json() as Record<string, unknown>;
    expect(body.status).toBe("ok");
  });

  it("returns a version string", async () => {
    const res = await GET();
    const body = await res.json() as Record<string, unknown>;
    expect(typeof body.version).toBe("string");
    expect((body.version as string).length).toBeGreaterThan(0);
  });

  it("returns a timestamp in ISO format", async () => {
    const res = await GET();
    const body = await res.json() as Record<string, unknown>;
    expect(typeof body.timestamp).toBe("string");
    expect(() => new Date(body.timestamp as string)).not.toThrow();
  });

  it("reports chat service as false when API key is missing", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "");
    const res = await GET();
    const body = await res.json() as { services: { chat: boolean } };
    expect(body.services.chat).toBe(false);
  });

  it("reports chat service as true when API key is present", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-test-key");
    const res = await GET();
    const body = await res.json() as { services: { chat: boolean } };
    expect(body.services.chat).toBe(true);
  });
});
