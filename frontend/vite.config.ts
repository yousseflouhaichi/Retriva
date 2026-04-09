import path from "path";
import { fileURLToPath } from "url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, "");
  const apiTarget = env.VITE_DEV_API_TARGET || "http://127.0.0.1:8080";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(rootDir, "./src"),
      },
    },
    server: {
      // Listen on all interfaces (0.0.0.0 / ::). Default "localhost" can bind IPv6-only on Windows while
      // cloudflared uses http://127.0.0.1:5173 (IPv4) -> 502 Bad Gateway.
      host: true,
      port: 5173,
      // Quick Tunnel hostnames (*.trycloudflare.com) are not localhost; allow them for demos.
      allowedHosts: true,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (requestPath) => {
            const stripped = requestPath.replace(/^\/api/, "");
            return stripped.length > 0 ? stripped : "/";
          },
        },
      },
    },
  };
});
