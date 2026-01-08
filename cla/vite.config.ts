import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(async () => ({
  plugins: [react()],

  // Vite options for Tauri
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      // workaround for Tauri
      ignored: ["**/src-tauri/**"],
    },
  },
}));
