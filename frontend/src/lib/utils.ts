import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;
  if (typeof raw !== "string" || raw.trim() === "") {
    throw new Error("VITE_API_URL must be set (see frontend/.env.example)");
  }
  return raw.replace(/\/$/, "");
}
