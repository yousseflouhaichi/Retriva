import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

function normalizeApiBase(trimmed: string): string {
  if (trimmed.startsWith("/")) {
    return trimmed.replace(/\/$/, "") || "";
  }
  return trimmed.replace(/\/$/, "");
}

/**
 * Dev server: defaults to `/api` so requests stay same-origin and Vite proxies to FastAPI (no browser CORS).
 * Production: `VITE_API_URL` is required (absolute URL or path).
 */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;
  if (import.meta.env.DEV) {
    if (typeof raw === "string" && raw.trim() !== "") {
      return normalizeApiBase(raw.trim());
    }
    return "/api";
  }
  if (typeof raw !== "string" || raw.trim() === "") {
    throw new Error("VITE_API_URL must be set for production builds (see frontend/.env.example)");
  }
  return normalizeApiBase(raw.trim());
}
