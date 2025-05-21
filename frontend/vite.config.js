import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Client-side routing configuration
const ClientSideRouting = {
  name: 'dynamic-router',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // Handle all routes except for static assets
      if (!req.url.startsWith('/assets/') && !req.url.includes('.')) {
        req.url = '/'
      }
      next()
    })
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), ClientSideRouting],
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    port: 5173,
    strictPort: true,
    host: true,
  }
})
