import path from "path";
import { fileURLToPath } from "url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, "");
  const apiTarget = env.VITE_DEV_API_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(rootDir, "./src"),
      },
    },
    server: {
      port: 5173,
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
