import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import glsl from 'vite-plugin-glsl'

export default defineConfig({
  plugins: [react(), tailwindcss(), glsl()],
  server: {
    port: 7751,
    proxy: {
      '/api': {
        target: 'http://localhost:7749',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws/chat': {
        target: 'ws://localhost:7749',
        ws: true,
      },
      '/ws/status': {
        target: 'ws://localhost:7749',
        ws: true,
      },
      '/ws/preview': {
        target: 'ws://localhost:7749',
        ws: true,
      },
    },
  },
})
