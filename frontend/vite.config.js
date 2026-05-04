import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/static/" : "/",
  plugins: [react()],
  build: {
    outDir: "../backend/frontend_dist",
    emptyOutDir: true,
  },
  server: {
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health/": "http://127.0.0.1:8000",
    },
  },
}));
