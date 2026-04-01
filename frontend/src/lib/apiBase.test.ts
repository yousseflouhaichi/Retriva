import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "./apiBase";

describe("resolveApiBaseUrl", () => {
  it("uses /api in development even when VITE_API_URL is a cross-origin URL", () => {
    expect(resolveApiBaseUrl(true, "http://127.0.0.1:8080")).toBe("/api");
    expect(resolveApiBaseUrl(true, "https://api.example.com")).toBe("/api");
  });

  it("uses /api in development when VITE_API_URL is unset", () => {
    expect(resolveApiBaseUrl(true, undefined)).toBe("/api");
    expect(resolveApiBaseUrl(true, "")).toBe("/api");
  });

  it("requires VITE_API_URL in production", () => {
    expect(() => resolveApiBaseUrl(false, undefined)).toThrow(/VITE_API_URL/);
    expect(() => resolveApiBaseUrl(false, "   ")).toThrow(/VITE_API_URL/);
  });

  it("normalizes production URL", () => {
    expect(resolveApiBaseUrl(false, "https://x.com/v1/")).toBe("https://x.com/v1");
  });

  it("allows same-site path in production", () => {
    expect(resolveApiBaseUrl(false, "/api")).toBe("/api");
  });
});
