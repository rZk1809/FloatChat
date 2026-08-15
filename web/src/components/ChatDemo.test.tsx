import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatDemo from "./ChatDemo";

afterEach(cleanup);

// jsdom doesn't implement scrollIntoView — mock it globally
beforeEach(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

// Mock localStorage
const store: Record<string, string> = {};
beforeEach(() => {
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v; },
    removeItem: (k: string) => { delete store[k]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  });
  // Reset store
  Object.keys(store).forEach((k) => delete store[k]);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// Mock fetch
function mockFetchSuccess(content: string) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ content }),
    ok: true,
  }));
}

function mockFetchError(errorMessage: string) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ error: errorMessage }),
    ok: false,
  }));
}

describe("ChatDemo", () => {
  it("renders the initial welcome message", () => {
    render(<ChatDemo />);
    expect(screen.getAllByText(/FloatChat/).length).toBeGreaterThan(0);
    expect(screen.getByRole("log")).toBeTruthy();
  });

  it("shows example query buttons initially", () => {
    render(<ChatDemo />);
    expect(screen.getByText(/T-S diagram/i)).toBeTruthy();
  });

  it("sends a message on button click", async () => {
    mockFetchSuccess("A T-S diagram plots temperature against salinity.");
    render(<ChatDemo />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "What is a T-S diagram?" } });

    const sendButton = screen.getByLabelText("Send message");
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText("What is a T-S diagram?")).toBeTruthy();
    });
  });

  it("displays assistant response after successful API call", async () => {
    mockFetchSuccess("A T-S diagram plots temperature against salinity.");
    render(<ChatDemo />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Explain T-S diagram" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/T-S diagram plots temperature/i)).toBeTruthy();
    });
  });

  it("shows system notice on API error response", async () => {
    mockFetchError("ANTHROPIC_API_KEY not configured.");
    render(<ChatDemo />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/System Notice/i)).toBeTruthy();
    });
  });

  it("shows error message on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    render(<ChatDemo />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/error connecting/i)).toBeTruthy();
    });
  });

  it("send button is disabled when input is empty", () => {
    render(<ChatDemo />);
    const sendButton = screen.getByLabelText("Send message");
    expect((sendButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("send button enables when input has content", () => {
    render(<ChatDemo />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Test message" } });
    const sendButton = screen.getByLabelText("Send message");
    expect((sendButton as HTMLButtonElement).disabled).toBe(false);
  });
});
