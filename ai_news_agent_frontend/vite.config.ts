import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig(({ mode }) => ({
  // 开发用 '/'，生产用 './'（部署到子目录时）
  base: mode === 'production' ? './' : '/',
  plugins: [react()],
  server: { port: 3000 },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./react_src"),
    },
  },
}))