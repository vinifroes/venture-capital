import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function normalizeBasePath(value) {
  if (!value || value.trim() === "") {
    return "/";
  }

  const trimmed = value.trim();
  if (trimmed === "/") {
    return "/";
  }

  return `/${trimmed.replace(/^\/+|\/+$/g, "")}/`;
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: normalizeBasePath(globalThis.process?.env?.VITE_BASE_PATH),
});
