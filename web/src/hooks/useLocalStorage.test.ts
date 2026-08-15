import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useLocalStorage } from "./useLocalStorage";

// Minimal localStorage mock
const store: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => { store[key] = value; },
  removeItem: (key: string) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
};

beforeEach(() => {
  localStorageMock.clear();
  vi.stubGlobal("localStorage", localStorageMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useLocalStorage", () => {
  it("returns initial value when nothing is stored", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", 42));
    expect(result.current.value).toBe(42);
  });

  it("persists a value to localStorage", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", 0));
    act(() => {
      result.current.setValue(99);
    });
    expect(result.current.value).toBe(99);
    expect(JSON.parse(localStorageMock.getItem("test-key") ?? "null")).toBe(99);
  });

  it("supports functional updates", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", 10));
    act(() => {
      result.current.setValue((prev) => prev + 5);
    });
    expect(result.current.value).toBe(15);
  });

  it("removes the value and resets to initial", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", "hello"));
    act(() => { result.current.setValue("world"); });
    act(() => { result.current.removeValue(); });
    expect(result.current.value).toBe("hello");
    expect(localStorageMock.getItem("test-key")).toBeNull();
  });

  it("handles JSON parse errors gracefully", () => {
    localStorageMock.setItem("bad-key", "not-valid-json{{{");
    const { result } = renderHook(() => useLocalStorage("bad-key", "fallback"));
    expect(result.current.value).toBe("fallback");
  });
});
