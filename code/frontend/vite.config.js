import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In local dev (npm run dev) /api is proxied to the backend on port 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/docs": "http://localhost:8000",
      "/openapi.json": "http://localhost:8000",
    },
  },
});
