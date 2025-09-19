import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server:{
    port: 5173,
    proxy: {
      // proxy API requests to backend during dev
      '/api': 'http://localhost:7860'
    }
  }
})
