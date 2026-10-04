import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@/components": path.resolve(__dirname, "./src/components"),
      "@/features": path.resolve(__dirname, "./src/features"),
      "@/lib": path.resolve(__dirname, "./src/lib"),
      "@/hooks": path.resolve(__dirname, "./src/hooks"),
      "@/api": path.resolve(__dirname, "./src/api"),
      "@/store": path.resolve(__dirname, "./src/store"),
      "@/utils": path.resolve(__dirname, "./src/utils"),
      "@/constants": path.resolve(__dirname, "./src/constants"),
      "@/routes": path.resolve(__dirname, "./src/routes"),
      "@/layouts": path.resolve(__dirname, "./src/layouts"),
      "@/styles": path.resolve(__dirname, "./src/styles"),
      "@/animations": path.resolve(__dirname, "./src/animations"),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    // No source maps in production builds: they published the full source
    // (3.4 MB). Vendor code is split out so no chunk passes the default
    // 500 kB warning (it was hidden by a 1000 kB limit).
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          data: ["@tanstack/react-query", "axios", "zustand"],
          markdown: ["react-markdown", "remark-gfm"],
        },
      },
    },
  },
});
